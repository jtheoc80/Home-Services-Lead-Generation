# Stripe Billing Smoke Tests

This document describes how to test the Stripe billing integration locally and in development.

## Prerequisites

1. **Stripe CLI installed**: Download from [stripe.com/docs/stripe-cli](https://stripe.com/docs/stripe-cli)
2. **Test Stripe account**: Use test keys (sk_test_*, pk_test_*)
3. **Local development environment**: Both frontend and backend running

## Local Development Setup

### 1. Environment Configuration

**Frontend (.env.local):**
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
INTERNAL_BACKEND_WEBHOOK_URL=http://localhost:8000/webhooks/stripe
INTERNAL_WEBHOOK_TOKEN=test-webhook-token
```

**Backend (.env):**
```bash
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PRICE_STARTER_MONTHLY=price_...
STRIPE_PRICE_PRO_MONTHLY=price_...
STRIPE_PRICE_LEAD_CREDIT_PACK=price_...
BILLING_SUCCESS_URL=http://localhost:3000/billing/success
BILLING_CANCEL_URL=http://localhost:3000/billing/cancel
INTERNAL_WEBHOOK_TOKEN=test-webhook-token
```

### 2. Start Development Servers

```bash
# Terminal 1: Backend
cd backend
python main.py

# Terminal 2: Frontend  
cd frontend
npm run dev

# Terminal 3: Stripe webhook forwarding
stripe login
stripe listen --forward-to http://localhost:3000/api/webhooks/stripe
```

## Manual Testing Steps

### 1. Health Checks

```bash
# Check backend health (should show stripe: "configured")
curl http://localhost:8000/healthz | jq

# Check frontend health (should show webhooksStripe: true)
curl http://localhost:3000/api/health | jq
```

### 2. Billing Page Access

1. Navigate to `http://localhost:3000/billing`
2. Verify plans are displayed correctly
3. Check credit balance section appears

### 3. Checkout Flow

1. Click "Subscribe to Starter Plan"
2. Should redirect to Stripe Checkout
3. Use test card: `4242 4242 4242 4242`
4. Complete checkout
5. Verify webhook event received in Stripe CLI terminal

### 4. Customer Portal

1. After completing a subscription, click "Manage Billing"
2. Should redirect to Stripe Customer Portal
3. Verify customer information and subscription details

### 5. Credit Purchase

1. Click "Buy Credits" 
2. Complete checkout with test card
3. Return to billing page
4. Verify credit balance increased by 50

## Webhook Testing

### Trigger Test Events

```bash
# Test successful subscription
stripe trigger checkout.session.completed

# Test invoice payment
stripe trigger invoice.paid

# Test subscription cancellation
stripe trigger customer.subscription.deleted

# Test payment failure
stripe trigger invoice.payment_failed
```

### Verify Webhook Processing

1. Check Stripe CLI output for 200 responses
2. Check backend logs for webhook processing
3. Verify database records:

```sql
-- Check billing events
SELECT type, event_id, created_at FROM billing_events ORDER BY created_at DESC LIMIT 5;

-- Check customer records
SELECT user_id, email, stripe_customer_id FROM billing_customers;

-- Check credit balances
SELECT user_id, balance, updated_at FROM lead_credits;
```

## Automated Testing Script

Run the smoke test script:

```bash
./scripts/stripe_smoke.sh
```

This script:
1. Starts the development servers
2. Waits for services to be ready
3. Triggers test webhook events
4. Verifies expected database changes
5. Reports success/failure

## Common Issues

### Webhook 401/404 Errors
- Check STRIPE_WEBHOOK_SECRET is set correctly
- Verify webhook endpoint URL is accessible
- Ensure Stripe CLI is forwarding to correct port

### Database Connection Errors
- Verify SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
- Check database tables exist (run migration)
- Verify service role has proper permissions

### Price ID Errors
- Run `python scripts/stripe_seed.py` to create products/prices
- Update environment variables with returned price IDs
- Verify price IDs exist in Stripe Dashboard

### Frontend Build Errors
- Check NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY is set
- Verify no server secrets in client code
- Clear Next.js cache: `rm -rf .next`

## Success Criteria

✅ All health checks return "ok" status  
✅ Billing page loads without errors  
✅ Checkout redirects to Stripe  
✅ Webhooks return 200 status  
✅ Database records created correctly  
✅ Customer portal accessible  
✅ Credit balances update properly