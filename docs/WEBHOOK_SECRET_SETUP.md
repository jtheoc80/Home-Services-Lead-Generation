# Webhook Secret Setup for Supabase Edge Functions

This document explains how to set up and use the `WEBHOOK_SECRET` environment variable for securing external webhooks to Supabase edge functions.

## Generate the Secret

Generate a 32+ character random string for use as a webhook secret:

```bash
openssl rand -hex 32
```

Example output:
```
4d8638ebc065d0e97be3a9787e695c226550212dd853505ad17c2cc2dc8b7f84
```

## Configuration

1. **Copy the secret to your environment:**
   ```bash
   # Copy this as WEBHOOK_SECRET
   WEBHOOK_SECRET=4d8638ebc065d0e97be3a9787e695c226550212dd853505ad17c2cc2dc8b7f84
   ```

2. **Add to Supabase Edge Function secrets:**
   ```bash
   supabase secrets set WEBHOOK_SECRET=your_generated_secret_here
   ```

3. **Update your `.env` file:**
   Copy `.env.example` to `.env` and replace the placeholder with your generated secret.

## Usage in Supabase Edge Functions

Here's an example of how to use the webhook secret in a Supabase edge function:

```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  try {
    // Verify webhook secret
    const webhookSecret = req.headers.get('x-webhook-secret')
    const expectedSecret = Deno.env.get('WEBHOOK_SECRET')
    
    if (!expectedSecret) {
      return new Response(
        JSON.stringify({ error: 'Webhook secret not configured' }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }
      )
    }

    if (!webhookSecret || webhookSecret !== expectedSecret) {
      return new Response(
        JSON.stringify({ error: 'Invalid webhook secret' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // Process webhook payload
    const payload = await req.json()
    
    // Your webhook logic here...
    
    return new Response(
      JSON.stringify({ success: true }),
      { headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: 'Internal server error' }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
})
```

## Security Notes

- **Never commit the actual secret to version control**
- **Store the secret securely in environment variables**
- **Use HTTPS for all webhook endpoints**
- **Consider implementing request timestamp validation for additional security**
- **Rotate the secret periodically**

## Environment Variable Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `WEBHOOK_SECRET` | Secret for authenticating external webhooks | `4d8638ebc065d0e97be3a9787e695c226550212dd853505ad17c2cc2dc8b7f84` |

## Related Files

- `.env.example` - Contains the webhook secret template