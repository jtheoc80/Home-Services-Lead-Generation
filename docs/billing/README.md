# Billing & Payments

This document explains the Stripe billing integration for LeadLedgerPro.

## Overview

The billing system provides:
- **Subscription Plans**: Monthly recurring billing for different contractor tiers
- **Credit Packs**: One-time purchases for additional lead credits
- **Customer Portal**: Self-service billing management
- **Webhooks**: Real-time payment and subscription updates
- **Credit System**: Track and consume lead credits

## Architecture

### Backend (Python FastAPI)
- `app/stripe_client.py` - Singleton Stripe client with configuration
- `app/billing_api.py` - Billing routes, webhooks, and credit management
- `app/lead_claims.py` - Lead claiming with credit consumption
- Database tables for customers, subscriptions, invoices, and credits

### Frontend (Next.js)
- `/billing` - Plan selection and credit purchase pages
- `/billing/success` - Payment confirmation page
- `/billing/cancel` - Payment cancellation page
- API proxy routes (no secrets exposed to client)

## Flows

### Subscription Flow
1. User selects a plan on `/billing`
2. Frontend calls `/api/billing/checkout/subscription`
3. Backend creates Stripe Checkout session
4. User completes payment on Stripe
5. Webhook updates subscription status and grants initial credits

### Credit Pack Flow
1. User clicks "Buy Credits" on `/billing`
2. Frontend calls `/api/billing/checkout/credits`
3. Backend creates one-time Checkout session
4. User completes payment on Stripe
5. Webhook grants credits to user's balance

### Lead Claiming Flow
1. User attempts to claim a lead
2. Backend checks credit balance via `use_credits()`
3. If sufficient, deducts 1 credit and records claim
4. If insufficient, returns 402 with upgrade CTA

## Configuration

### Environment Variables

**Backend (.env)**
```bash
STRIPE_SECRET_KEY=sk_test_xxx                    # Server-side operations
STRIPE_WEBHOOK_SECRET=whsec_xxx                  # Webhook signature verification
STRIPE_PUBLISHABLE_KEY=pk_test_xxx               # For frontend (if needed server-side)
STRIPE_PRICE_STARTER_MONTHLY=price_xxx           # Starter plan price ID
STRIPE_PRICE_PRO_MONTHLY=price_xxx               # Pro plan price ID  
STRIPE_PRICE_LEAD_CREDIT_PACK=price_xxx          # Credit pack price ID
STRIPE_TAX_RATE_ID=txr_xxx                       # Optional tax rate
BILLING_SUCCESS_URL=https://domain.com/billing/success
BILLING_CANCEL_URL=https://domain.com/billing/cancel
```

**Frontend (.env.local)**
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx   # Client-side Stripe.js
```

### Database Schema

The billing tables are automatically created via `make db-billing`:

- `billing_customers` - Maps users to Stripe customer IDs
- `billing_subscriptions` - Tracks active subscriptions
- `billing_invoices` - Invoice history and status
- `lead_credits` - User credit balances
- `billing_events` - Webhook event log
- `lead_claims` - Claimed leads with credit consumption

## API Endpoints

### Billing Management
- `POST /api/billing/create-customer` - Create/get Stripe customer
- `POST /api/billing/checkout/subscription` - Create subscription checkout
- `POST /api/billing/checkout/credits` - Create credit pack checkout
- `POST /api/billing/portal` - Customer portal session
- `GET /api/billing/credits` - Get current credit balance

### Webhooks
- `POST /webhooks/stripe` - Handle Stripe events

### Lead Management
- `POST /api/leads/claim` - Claim lead using credits
- `GET /api/leads/claims` - Get user's claimed leads

## Development

### Setup Products & Prices
```bash
# 1. Configure Stripe keys in backend/.env
# 2. Seed products and prices
make billing-seed

# Output will show price IDs to add to .env
```

### Local Development
```bash
# Start backend and webhook forwarding
make billing-webhook

# In another terminal, trigger test events
stripe trigger checkout.session.completed
stripe trigger invoice.paid
```

### Testing
```bash
# Run billing-specific tests
make billing-test

# Run all tests
make test
```

## Security

### Secret Management
- ❌ **Never** expose `STRIPE_SECRET_KEY` or `STRIPE_WEBHOOK_SECRET` to the frontend
- ✅ Only `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` is safe for client-side use
- ✅ All payment processing happens server-side
- ✅ Webhooks use signature verification

### Webhook Security
- All webhook events require valid Stripe signatures
- Idempotency prevents duplicate processing
- Events are logged to `billing_events` for auditing

### Credit Security
- Credits can only be consumed through authenticated API calls
- Database constraints prevent negative balances
- All credit transactions are logged

## Business Logic

### Plans
- **Starter ($199/month)**: 25 leads, Houston metro, basic features
- **Pro ($399/month)**: 100 leads, Texas statewide, advanced features
- **Credit Pack ($49)**: 50 additional lead credits

### Credit Usage
- Each lead claim consumes 1 credit
- Subscribers get monthly credit allowances
- Credit packs provide extra credits for any user
- Credits never expire

### Subscription Management
- Users can upgrade/downgrade via Customer Portal
- Cancellations take effect at period end
- Failed payments trigger email notifications

## Monitoring

The `/healthz` endpoint includes Stripe connectivity:
```json
{
  "status": "ok",
  "stripe": "configured|missing|error|timeout"
}
```

## Troubleshooting

### Webhook Issues
1. Check `STRIPE_WEBHOOK_SECRET` is correct
2. Verify webhook endpoint is accessible
3. Check `billing_events` table for logged events
4. Test with `stripe trigger` commands

### Credit Issues
1. Check `lead_credits` table for user balance
2. Verify subscription status in `billing_subscriptions`
3. Check `billing_events` for recent webhook activity
4. Manually grant credits: `INSERT INTO lead_credits ...`

### Failed Payments
1. Check `billing_invoices` for payment status
2. Verify subscription status updates
3. User should receive Stripe email notifications
4. Customer Portal allows payment method updates

## Support Contacts

- **Stripe Dashboard**: [dashboard.stripe.com](https://dashboard.stripe.com)
- **Webhook Logs**: Dashboard → Developers → Webhooks
- **Customer Portal**: Users can self-service via billing page