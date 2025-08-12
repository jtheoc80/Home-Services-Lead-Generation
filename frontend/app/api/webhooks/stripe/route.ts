import { NextRequest, NextResponse } from 'next/server';
import { headers } from 'next/headers';

/**
 * Vercel Stripe Webhook Handler (App Router)
 * 
 * Handles Stripe webhook events with signature verification and processing.
 * Forwards authenticated requests to the Railway backend for database updates.
 */

// Disable Next.js body parsing to get raw body for signature verification
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    // Get environment variables
    const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
    const internalWebhookUrl = process.env.INTERNAL_BACKEND_WEBHOOK_URL;
    const internalToken = process.env.INTERNAL_WEBHOOK_TOKEN;
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!webhookSecret) {
      console.error('STRIPE_WEBHOOK_SECRET not configured');
      return NextResponse.json({ error: 'Webhook not configured' }, { status: 500 });
    }

    // Get raw body and signature
    const body = await request.text();
    const signature = request.headers.get('stripe-signature');

    if (!signature) {
      console.error('Missing Stripe signature');
      return NextResponse.json({ error: 'Missing signature' }, { status: 400 });
    }

    // Lazy load stripe to avoid build-time issues
    const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

    // Verify webhook signature
    let event;
    try {
    // Lazy load Stripe to avoid build-time issues
    const Stripe = require('stripe');

    // Verify webhook signature
    let event;
    try {
      event = Stripe.webhooks.constructEvent(body, signature, webhookSecret);
    } catch (err: any) {
      console.error('Webhook signature verification failed:', err.message);
      return NextResponse.json({ error: 'Invalid signature' }, { status: 400 });
    }

    // Log event type and ID for debugging
    console.log(`Received Stripe webhook: ${event.type} (${event.id})`);

    // Check for duplicate events (idempotency)
    if (supabaseUrl && supabaseServiceKey) {
      // Lazy load supabase to avoid build-time issues
      const { createClient } = await import('@supabase/supabase-js');
      const supabase = createClient(supabaseUrl, supabaseServiceKey);
      
      try {
        // Check if event already exists
        const { data: existingEvent } = await supabase
          .table('billing_events')
          .select('id')
          .eq('event_id', event.id)
          .single();

        if (existingEvent) {
          console.log(`Duplicate event ${event.id}, skipping`);
          return NextResponse.json({ status: 'duplicate', received: true });
        }

        // Store event for idempotency
        await supabase
          .table('billing_events')
          .insert({
            type: event.type,
            event_id: event.id,
            payload: event,
            created_at: new Date().toISOString()
          });

      } catch (error) {
        console.error('Error checking/storing event idempotency:', error);
        // Continue processing even if idempotency check fails
      }
    }

    // Process supported events
    const supportedEvents = [
      'checkout.session.completed',
      'invoice.paid',
      'invoice.payment_failed',
      'customer.subscription.updated',
      'customer.subscription.deleted'
    ];

    if (supportedEvents.includes(event.type)) {
      // Forward to Railway backend if configured
      if (internalWebhookUrl && internalToken) {
        try {
          const response = await fetch(internalWebhookUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${internalToken}`,
              'X-Event-Type': event.type,
              'X-Event-ID': event.id
            },
            body: JSON.stringify(event)
          });

          if (!response.ok) {
            console.error(`Backend webhook failed: ${response.status} ${response.statusText}`);
          } else {
            console.log(`Successfully forwarded ${event.type} to backend`);
          }
        } catch (error) {
          console.error('Error forwarding to backend webhook:', error);
        }
      }

      // Process critical events locally for fast response
      if (supabaseUrl && supabaseServiceKey) {
        await processEventLocally(event, supabaseUrl, supabaseServiceKey);
      }
    } else {
      console.log(`Unhandled event type: ${event.type}`);
    }

    // Return 200 quickly
    return NextResponse.json({ 
      status: 'success', 
      received: true, 
      event_type: event.type,
      event_id: event.id 
    });

  } catch (error) {
    console.error('Webhook processing error:', error);
    return NextResponse.json(
      { error: 'Webhook processing failed' }, 
      { status: 500 }
    );
  }
}

/**
 * Process events locally using Supabase for critical updates
 */
async function processEventLocally(event: any, supabaseUrl: string, supabaseServiceKey: string) {
  // Lazy load supabase to avoid build-time issues
  const { createClient } = await import('@supabase/supabase-js');
  const supabase = createClient(supabaseUrl, supabaseServiceKey);

  try {
    switch (event.type) {
      case 'checkout.session.completed':
        await handleCheckoutCompleted(event.data.object, supabase);
        break;
      
      case 'customer.subscription.updated':
      case 'customer.subscription.deleted':
        await handleSubscriptionUpdate(event.data.object, supabase);
        break;
      
      case 'invoice.paid':
        await handleInvoicePaid(event.data.object, supabase);
        break;
      
      case 'invoice.payment_failed':
        await handleInvoiceFailed(event.data.object, supabase);
        break;
    }
  } catch (error) {
    console.error(`Error processing ${event.type} locally:`, error);
  }
}

async function handleCheckoutCompleted(session: any, supabase: any) {
  const userId = session.metadata?.user_id;
  if (!userId) return;

  // Update customer record
  if (session.customer) {
    await supabase
      .table('billing_customers')
      .upsert({
        user_id: userId,
        stripe_customer_id: session.customer,
        updated_at: new Date().toISOString()
      }, { onConflict: 'user_id' });
  }

  // Handle credit pack purchase
  if (session.metadata?.type === 'credit_pack' && session.mode === 'payment') {
    // Grant credits (configurable)
    const creditPackAmount = parseInt(process.env.CREDIT_PACK_AMOUNT || "50", 10);
    await supabase
      .table('lead_credits')
      .upsert({
        user_id: userId,
        balance: supabase.raw(`COALESCE(balance, 0) + ${creditPackAmount}`),
        updated_at: new Date().toISOString()
      }, { onConflict: 'user_id' });
  }
}

async function handleSubscriptionUpdate(subscription: any, supabase: any) {
  await supabase
    .table('billing_subscriptions')
    .upsert({
      stripe_subscription_id: subscription.id,
      status: subscription.status,
      current_period_end: new Date(subscription.current_period_end * 1000).toISOString(),
      cancel_at_period_end: subscription.cancel_at_period_end || false,
      updated_at: new Date().toISOString()
    }, { onConflict: 'stripe_subscription_id' });
}

async function handleInvoicePaid(invoice: any, supabase: any) {
  await supabase
    .table('billing_invoices')
    .upsert({
      stripe_invoice_id: invoice.id,
      user_id: invoice.metadata?.user_id || 'unknown',
      amount_due: invoice.amount_due,
      amount_paid: invoice.amount_paid,
      status: invoice.status,
      hosted_invoice_url: invoice.hosted_invoice_url,
      created_at: new Date().toISOString()
    }, { onConflict: 'stripe_invoice_id' });
}

async function handleInvoiceFailed(invoice: any, supabase: any) {
  await handleInvoicePaid(invoice, supabase); // Same logic, different status
}
}