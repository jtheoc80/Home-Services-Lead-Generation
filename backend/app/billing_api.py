"""
Billing API routes for Stripe payment processing.

This module provides FastAPI routes for:
- Creating Stripe customers
- Checkout sessions for subscriptions and credit packs
- Customer portal sessions
- Webhook handling for Stripe events
- Credit management functions
"""

import os
import logging
from typing import Dict, Optional
from datetime import datetime, timezone

import stripe
from fastapi import HTTPException, Request, Header, Depends
from pydantic import BaseModel

from .auth import AuthUser, auth_user
from .stripe_client import get_stripe_client
from .supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# Pydantic models for request/response validation
class CheckoutSessionRequest(BaseModel):
    price_id: str
    quantity: Optional[int] = 1

class CustomerResponse(BaseModel):
    customer_id: str
    email: str

class CheckoutSessionResponse(BaseModel):
    checkout_url: str
    session_id: str

class PortalSessionResponse(BaseModel):
    portal_url: str

class CreditBalance(BaseModel):
    user_id: str
    balance: int
    updated_at: str

# Credit management functions
async def grant_credits(user_id: str, quantity: int) -> bool:
    """
    Safely increment lead credits for a user in a transaction.
    
    Args:
        user_id: User UUID
        quantity: Number of credits to add
        
    Returns:
        True if credits were granted successfully
    """
    try:
        client = get_supabase_client()
        
        # Upsert credits (insert or update)
        result = client.table("lead_credits").upsert({
            "user_id": user_id,
            "balance": f"coalesce(balance, 0) + {quantity}",  # Raw SQL expression
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="user_id").execute()
        
        logger.info(f"Granted {quantity} credits to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to grant credits to user {user_id}: {e}")
        return False

async def use_credits(user_id: str, quantity: int) -> bool:
    """
    Attempt to use credits for a user. Returns False if insufficient credits.
    
    Args:
        user_id: User UUID
        quantity: Number of credits to use
        
    Returns:
        True if credits were used successfully, False if insufficient
    """
    try:
        client = get_supabase_client()
        
        # First, check current balance
        result = client.table("lead_credits").select("balance").eq("user_id", user_id).execute()
        
        if not result.data:
            # No credit record exists
            logger.warning(f"No credit record found for user {user_id}")
            return False
        
        current_balance = result.data[0]["balance"]
        if current_balance < quantity:
            logger.warning(f"Insufficient credits for user {user_id}: {current_balance} < {quantity}")
            return False
        
        # Deduct credits
        new_balance = current_balance - quantity
        client.table("lead_credits").update({
            "balance": new_balance,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("user_id", user_id).execute()
        
        logger.info(f"Used {quantity} credits for user {user_id}, new balance: {new_balance}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to use credits for user {user_id}: {e}")
        return False

async def get_credit_balance(user_id: str) -> int:
    """Get the current credit balance for a user."""
    try:
        client = get_supabase_client()
        result = client.table("lead_credits").select("balance").eq("user_id", user_id).execute()
        
        if result.data:
            return result.data[0]["balance"]
        return 0
        
    except Exception as e:
        logger.error(f"Failed to get credit balance for user {user_id}: {e}")
        return 0

# Billing API route handlers
async def create_customer(user: AuthUser = Depends(auth_user)) -> CustomerResponse:
    """
    Create or retrieve a Stripe customer for the authenticated user.
    """
    try:
        client = get_supabase_client()
        stripe_client = get_stripe_client()
        
        # Check if customer already exists
        result = client.table("billing_customers").select("*").eq("user_id", user.account_id).execute()
        
        if result.data:
            # Customer already exists
            customer_data = result.data[0]
            return CustomerResponse(
                customer_id=customer_data["stripe_customer_id"],
                email=customer_data["email"]
            )
        
        # Create new Stripe customer
        stripe_customer = stripe.Customer.create(
            email=user.email,
            metadata={"user_id": user.account_id}
        )
        
        # Store in database
        client.table("billing_customers").insert({
            "user_id": user.account_id,
            "email": user.email,
            "stripe_customer_id": stripe_customer.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"Created Stripe customer {stripe_customer.id} for user {user.account_id}")
        
        return CustomerResponse(
            customer_id=stripe_customer.id,
            email=user.email
        )
        
    except Exception as e:
        logger.error(f"Failed to create customer for user {user.account_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create customer")

async def create_checkout_session_subscription(
    request: CheckoutSessionRequest,
    user: AuthUser = Depends(auth_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout session for subscription.
    """
    try:
        stripe_client = get_stripe_client()
        
        # Ensure customer exists
        customer_response = await create_customer(user)
        
        # Create checkout session
        session_params = {
            "customer": customer_response.customer_id,
            "payment_method_types": ["card"],
            "line_items": [{
                "price": request.price_id,
                "quantity": request.quantity,
            }],
            "mode": "subscription",
            "success_url": stripe_client.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": stripe_client.cancel_url,
            "metadata": {
                "user_id": user.account_id
            }
        }
        
        if idempotency_key:
            session_params["idempotency_key"] = idempotency_key
            
        session = stripe.checkout.Session.create(**session_params)
        
        logger.info(f"Created subscription checkout session {session.id} for user {user.account_id}")
        
        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except Exception as e:
        logger.error(f"Failed to create subscription checkout for user {user.account_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

async def create_checkout_session_credits(
    user: AuthUser = Depends(auth_user),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> CheckoutSessionResponse:
    """
    Create a Stripe Checkout session for lead credit pack purchase.
    """
    try:
        stripe_client = get_stripe_client()
        
        if not stripe_client.price_lead_credit_pack:
            raise HTTPException(status_code=400, detail="Lead credit pack price not configured")
        
        # Ensure customer exists
        customer_response = await create_customer(user)
        
        # Create checkout session for one-time payment
        session_params = {
            "customer": customer_response.customer_id,
            "payment_method_types": ["card"],
            "line_items": [{
                "price": stripe_client.price_lead_credit_pack,
                "quantity": 1,
            }],
            "mode": "payment",
            "success_url": stripe_client.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            "cancel_url": stripe_client.cancel_url,
            "metadata": {
                "user_id": user.account_id,
                "type": "credit_pack"
            }
        }
        
        if idempotency_key:
            session_params["idempotency_key"] = idempotency_key
            
        session = stripe.checkout.Session.create(**session_params)
        
        logger.info(f"Created credit pack checkout session {session.id} for user {user.account_id}")
        
        return CheckoutSessionResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except Exception as e:
        logger.error(f"Failed to create credit checkout for user {user.account_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")

async def create_portal_session(user: AuthUser = Depends(auth_user)) -> PortalSessionResponse:
    """
    Create a Stripe Customer Portal session for managing billing.
    """
    try:
        # Ensure customer exists
        customer_response = await create_customer(user)
        
        # Create portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_response.customer_id,
            return_url=os.getenv("BILLING_SUCCESS_URL", "https://localhost:3000/billing")
        )
        
        logger.info(f"Created portal session for user {user.account_id}")
        
        return PortalSessionResponse(portal_url=session.url)
        
    except Exception as e:
        logger.error(f"Failed to create portal session for user {user.account_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")

async def handle_webhook(request: Request) -> Dict[str, str]:
    """
    Handle Stripe webhook events with signature verification.
    """
    try:
        stripe_client = get_stripe_client()
        
        if not stripe_client.webhook_secret:
            raise HTTPException(status_code=500, detail="Webhook secret not configured")
        
        # Get raw body and signature
        body = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                body, sig_header, stripe_client.webhook_secret
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Log the event for idempotency (check for duplicates)
        client = get_supabase_client()
        
        # Check if event already exists
        existing_event = client.table("billing_events").select("id").eq("event_id", event["id"]).execute()
        if existing_event.data:
            logger.info(f"Duplicate webhook event {event['id']}, skipping")
            return {"status": "duplicate", "received": True}
        
        # Store new event
        client.table("billing_events").insert({
            "type": event["type"],
            "event_id": event["id"],
            "payload": event,
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        # Handle specific event types
        if event["type"] == "checkout.session.completed":
            await handle_checkout_completed(event["data"]["object"])
        elif event["type"] == "invoice.paid":
            await handle_invoice_paid(event["data"]["object"])
        elif event["type"] == "invoice.payment_failed":
            await handle_invoice_failed(event["data"]["object"])
        elif event["type"] in ["customer.subscription.updated", "customer.subscription.deleted"]:
            await handle_subscription_updated(event["data"]["object"])
        
        logger.info(f"Processed webhook event {event['id']} of type {event['type']}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def handle_checkout_completed(session):
    """Handle successful checkout completion."""
    try:
        client = get_supabase_client()
        user_id = session.get("metadata", {}).get("user_id")
        
        if not user_id:
            logger.warning("No user_id in checkout session metadata")
            return
        
        # Update or create customer record
        customer_id = session.get("customer")
        if customer_id:
            client.table("billing_customers").upsert({
                "user_id": user_id,
                "stripe_customer_id": customer_id,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }, on_conflict="user_id").execute()
        
        # Handle subscription
        if session.get("mode") == "subscription":
            subscription_id = session.get("subscription")
            if subscription_id:
                # Get subscription details from Stripe
                subscription = stripe.Subscription.retrieve(subscription_id)
                
                client.table("billing_subscriptions").upsert({
                    "user_id": user_id,
                    "stripe_subscription_id": subscription_id,
                    "status": subscription.status,
                    "price_id": subscription["items"]["data"][0]["price"]["id"],
                    "quantity": subscription["items"]["data"][0]["quantity"],
                    "current_period_end": datetime.fromtimestamp(
                        subscription.current_period_end, tz=timezone.utc
                    ).isoformat(),
                    "cancel_at_period_end": subscription.cancel_at_period_end,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }, on_conflict="stripe_subscription_id").execute()
        
        # Handle credit pack purchase
        elif session.get("metadata", {}).get("type") == "credit_pack":
            # Grant 50 credits for credit pack purchase (configure as needed)
            await grant_credits(user_id, 50)
        
        logger.info(f"Processed checkout completion for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to handle checkout completion: {e}")

async def handle_invoice_paid(invoice):
    """Handle successful invoice payment."""
    try:
        client = get_supabase_client()
        user_id = invoice.get("metadata", {}).get("user_id")
        
        # Store invoice record
        client.table("billing_invoices").upsert({
            "stripe_invoice_id": invoice["id"],
            "user_id": user_id or "unknown",
            "amount_due": invoice["amount_due"],
            "amount_paid": invoice["amount_paid"],
            "status": invoice["status"],
            "hosted_invoice_url": invoice.get("hosted_invoice_url"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="stripe_invoice_id").execute()
        
        logger.info(f"Processed invoice payment {invoice['id']}")
        
    except Exception as e:
        logger.error(f"Failed to handle invoice payment: {e}")

async def handle_invoice_failed(invoice):
    """Handle failed invoice payment."""
    try:
        client = get_supabase_client()
        
        # Store invoice record
        client.table("billing_invoices").upsert({
            "stripe_invoice_id": invoice["id"],
            "user_id": invoice.get("metadata", {}).get("user_id", "unknown"),
            "amount_due": invoice["amount_due"],
            "amount_paid": invoice["amount_paid"],
            "status": invoice["status"],
            "hosted_invoice_url": invoice.get("hosted_invoice_url"),
            "created_at": datetime.now(timezone.utc).isoformat()
        }, on_conflict="stripe_invoice_id").execute()
        
        # Update subscription status if needed
        subscription_id = invoice.get("subscription")
        if subscription_id:
            client.table("billing_subscriptions").update({
                "status": "past_due",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("stripe_subscription_id", subscription_id).execute()
        
        logger.warning(f"Processed failed invoice payment {invoice['id']}")
        
    except Exception as e:
        logger.error(f"Failed to handle invoice failure: {e}")

async def handle_subscription_updated(subscription):
    """Handle subscription updates or cancellations."""
    try:
        client = get_supabase_client()
        
        client.table("billing_subscriptions").update({
            "status": subscription["status"],
            "current_period_end": datetime.fromtimestamp(
                subscription["current_period_end"], tz=timezone.utc
            ).isoformat(),
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("stripe_subscription_id", subscription["id"]).execute()
        
        logger.info(f"Updated subscription {subscription['id']}")
        
    except Exception as e:
        logger.error(f"Failed to handle subscription update: {e}")

async def get_user_credits(user: AuthUser = Depends(auth_user)) -> CreditBalance:
    """Get the current credit balance for the authenticated user."""
    balance = await get_credit_balance(user.account_id)
    return CreditBalance(
        user_id=user.account_id,
        balance=balance,
        updated_at=datetime.now(timezone.utc).isoformat()
    )