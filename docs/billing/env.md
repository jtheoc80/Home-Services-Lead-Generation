# Billing Environment Variables

This document explains where each Stripe billing environment variable should be configured.

## Vercel (Frontend & Webhook Handler)

These variables are configured in the Vercel dashboard for the frontend deployment:

| Variable | Purpose | Example |
|----------|---------|---------|
| `STRIPE_WEBHOOK_SECRET` | Webhook signature verification | `whsec_xxx` |
| `INTERNAL_BACKEND_WEBHOOK_URL` | Railway backend webhook endpoint | `https://your-app.railway.app/api/billing/webhook` |
| `INTERNAL_WEBHOOK_TOKEN` | Secure token for webhook forwarding | `shared-secret-token` |
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key for database operations | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` | Client-safe Stripe key | `pk_test_xxx` or `pk_live_xxx` |

## Railway (Backend API)

These variables are configured in the Railway dashboard for the backend deployment:

| Variable | Purpose | Example |
|----------|---------|---------|
| `STRIPE_SECRET_KEY` | Server-side Stripe operations | `sk_test_xxx` or `sk_live_xxx` |
| `STRIPE_PRICE_STARTER_MONTHLY` | Starter plan price ID | `price_1ABC123` |
| `STRIPE_PRICE_PRO_MONTHLY` | Pro plan price ID | `price_1DEF456` |
| `STRIPE_PRICE_LEAD_CREDIT_PACK` | Credit pack price ID | `price_1GHI789` |
| `BILLING_SUCCESS_URL` | Post-checkout success redirect | `https://your-app.vercel.app/billing/success` |
| `BILLING_CANCEL_URL` | Post-checkout cancel redirect | `https://your-app.vercel.app/billing/cancel` |
| `INTERNAL_WEBHOOK_TOKEN` | Same token as Vercel for authentication | `shared-secret-token` |

## Local Development

For local development, copy the example files and configure:

- **Frontend**: `frontend/.env.local` (gitignored)
- **Backend**: `backend/.env` (gitignored)

## Security Notes

- **Never** expose server secrets (`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`) to the frontend
- Only `NEXT_PUBLIC_*` prefixed variables are safe for browser exposure
- The `INTERNAL_WEBHOOK_TOKEN` should be a strong, shared secret between Vercel and Railway
- Use test keys during development and live keys only in production