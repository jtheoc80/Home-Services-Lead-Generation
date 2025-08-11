# Billing Runbooks

Incident response procedures for billing and payment issues.

## 🚨 Webhook Failures

### Symptoms
- Payments completed but subscriptions not activated
- Credits purchased but not granted to users
- Subscription changes not reflected in database

### Diagnosis
1. **Check Stripe Dashboard**
   - Go to Developers → Webhooks
   - Look for failed webhook attempts (red indicators)
   - Check error messages and response codes

2. **Check Application Logs**
   ```bash
   # Backend logs for webhook processing
   grep "webhook" /path/to/backend.log
   grep "billing_api" /path/to/backend.log
   ```

3. **Check Database**
   ```sql
   -- Check if events are being logged
   SELECT type, created_at FROM billing_events 
   ORDER BY created_at DESC LIMIT 10;
   
   -- Check for missing webhook events
   SELECT * FROM billing_events 
   WHERE type = 'checkout.session.completed' 
   AND created_at > NOW() - INTERVAL '1 hour';
   ```

### Resolution
1. **Verify Webhook Configuration**
   ```bash
   # Check webhook secret is correct
   echo $STRIPE_WEBHOOK_SECRET
   
   # Test webhook endpoint
   curl -X POST https://your-api.com/webhooks/stripe \
     -H "Content-Type: application/json" \
     -d '{"test": true}'
   ```

2. **Manually Replay Events**
   - In Stripe Dashboard → Developers → Webhooks
   - Click on failed event
   - Click "Resend Event"
   - Monitor application logs for processing

3. **Manual Data Correction**
   ```sql
   -- If subscription webhook failed, manually update
   INSERT INTO billing_subscriptions (
     user_id, stripe_subscription_id, status, 
     price_id, current_period_end, created_at
   ) VALUES (
     'user-id', 'sub_xxx', 'active',
     'price_xxx', '2024-02-01', NOW()
   );
   
   -- If credit pack webhook failed, manually grant credits
   INSERT INTO lead_credits (user_id, balance, updated_at)
   VALUES ('user-id', 50, NOW())
   ON CONFLICT (user_id) DO UPDATE SET
     balance = lead_credits.balance + 50,
     updated_at = NOW();
   ```

## 💳 Failed Payments

### Symptoms
- User reports subscription cancelled unexpectedly
- Lead claiming returns "insufficient credits"
- Customer portal shows past due status

### Diagnosis
1. **Check Stripe Customer Portal**
   - Search for customer by email in Stripe Dashboard
   - Review payment history and failed charges
   - Check subscription status

2. **Check Application Database**
   ```sql
   -- Check subscription status
   SELECT * FROM billing_subscriptions 
   WHERE user_id = 'user-id';
   
   -- Check recent invoices
   SELECT * FROM billing_invoices 
   WHERE user_id = 'user-id' 
   ORDER BY created_at DESC;
   ```

### Resolution
1. **Customer Self-Service**
   - Direct user to `/billing` page
   - Click "Manage Billing" to access Customer Portal
   - User can update payment method and retry payment

2. **Manual Invoice Recovery**
   - In Stripe Dashboard, find failed invoice
   - Click "Resend invoice" to customer
   - Or manually mark as paid if payment received elsewhere

3. **Subscription Reactivation**
   ```sql
   -- If payment successful but status not updated
   UPDATE billing_subscriptions 
   SET status = 'active', updated_at = NOW()
   WHERE stripe_subscription_id = 'sub_xxx';
   ```

## 🔄 Subscription State Mismatch

### Symptoms
- Stripe shows active subscription but app shows cancelled
- User has active subscription but no credits
- Features not unlocked despite active subscription

### Diagnosis
1. **Compare Stripe vs Database**
   ```bash
   # Get subscription from Stripe API
   stripe subscriptions retrieve sub_xxx
   ```
   
   ```sql
   -- Get subscription from database
   SELECT * FROM billing_subscriptions 
   WHERE stripe_subscription_id = 'sub_xxx';
   ```

2. **Check Recent Webhook Events**
   ```sql
   SELECT type, payload, created_at 
   FROM billing_events 
   WHERE payload->>'subscription' = 'sub_xxx'
   ORDER BY created_at DESC;
   ```

### Resolution
1. **Sync from Stripe**
   ```python
   # Python script to sync subscription data
   import stripe
   
   stripe.api_key = "sk_test_xxx"
   subscription = stripe.Subscription.retrieve("sub_xxx")
   
   # Update database with current Stripe data
   # (implement database update logic)
   ```

2. **Manual Database Update**
   ```sql
   UPDATE billing_subscriptions SET
     status = 'active',
     current_period_end = '2024-02-01 00:00:00',
     cancel_at_period_end = false,
     updated_at = NOW()
   WHERE stripe_subscription_id = 'sub_xxx';
   ```

## 🏦 Credit Balance Issues

### Symptoms
- User purchased credits but balance not updated
- Credits deducted but lead claim failed
- Negative credit balance (should be impossible)

### Diagnosis
1. **Check Credit History**
   ```sql
   -- Current balance
   SELECT balance FROM lead_credits WHERE user_id = 'user-id';
   
   -- Recent credit-related events
   SELECT type, payload, created_at FROM billing_events
   WHERE payload->>'metadata'->>'user_id' = 'user-id'
   AND type IN ('checkout.session.completed', 'invoice.paid');
   
   -- Recent lead claims
   SELECT * FROM lead_claims 
   WHERE user_id = 'user-id' 
   ORDER BY claimed_at DESC LIMIT 10;
   ```

2. **Check Purchase History**
   - Look for recent `checkout.session.completed` events
   - Verify credit pack purchases in Stripe Dashboard

### Resolution
1. **Manual Credit Grant**
   ```sql
   -- Grant missing credits
   INSERT INTO lead_credits (user_id, balance, updated_at)
   VALUES ('user-id', 50, NOW())
   ON CONFLICT (user_id) DO UPDATE SET
     balance = lead_credits.balance + 50,
     updated_at = NOW();
   ```

2. **Credit Correction**
   ```sql
   -- Fix incorrect balance
   UPDATE lead_credits 
   SET balance = 25, updated_at = NOW()
   WHERE user_id = 'user-id';
   ```

3. **Audit Trail**
   ```sql
   -- Log manual credit adjustment
   INSERT INTO billing_events (type, payload, created_at)
   VALUES (
     'manual.credit_adjustment',
     '{"user_id": "user-id", "amount": 50, "reason": "webhook_failure", "admin": "admin-email"}',
     NOW()
   );
   ```

## 🔍 Reconciliation Procedures

### Daily Reconciliation
1. **Compare Stripe vs Database Counts**
   ```sql
   -- Count active subscriptions in database
   SELECT COUNT(*) FROM billing_subscriptions WHERE status = 'active';
   ```
   
   ```bash
   # Count active subscriptions in Stripe
   stripe subscriptions list --status=active --limit=100 | jq '.data | length'
   ```

2. **Check for Missing Webhook Events**
   ```sql
   -- Find gaps in webhook events (should be continuous)
   SELECT DATE(created_at) as event_date, COUNT(*) as event_count
   FROM billing_events 
   WHERE created_at > NOW() - INTERVAL '7 days'
   GROUP BY DATE(created_at)
   ORDER BY event_date;
   ```

### Weekly Reconciliation
1. **Credit Usage Analysis**
   ```sql
   -- Users with high credit usage
   SELECT user_id, COUNT(*) as claims_this_week
   FROM lead_claims 
   WHERE claimed_at > NOW() - INTERVAL '7 days'
   GROUP BY user_id
   ORDER BY claims_this_week DESC;
   ```

2. **Revenue Reconciliation**
   ```sql
   -- Compare invoice totals vs Stripe revenue
   SELECT 
     DATE(created_at) as invoice_date,
     SUM(amount_paid) / 100.0 as total_revenue
   FROM billing_invoices 
   WHERE status = 'paid' 
   AND created_at > NOW() - INTERVAL '7 days'
   GROUP BY DATE(created_at);
   ```

## 📞 Customer Support Scripts

### "My payment went through but I don't have access"
1. Look up customer by email in Stripe Dashboard
2. Check subscription status and recent invoices
3. Check database subscription record
4. If mismatch, sync from Stripe or manually update
5. If webhook issue, replay the event

### "I was charged but my credits weren't added"
1. Find the payment in Stripe Dashboard
2. Check for corresponding webhook event in `billing_events`
3. If event missing, manually replay webhook
4. If event present, manually grant credits
5. Add audit log entry

### "My subscription was cancelled but I didn't cancel it"
1. Check for failed payment in Stripe
2. Guide user to Customer Portal to update payment method
3. If payment method valid, check for webhook issues
4. Manually reactivate subscription if appropriate

## 🚨 Emergency Procedures

### Complete Webhook Failure
1. **Immediate Response**
   - Set up monitoring alert
   - Document start time and scope
   - Notify technical team

2. **Temporary Mitigation**
   - Manually process critical payments
   - Grant credits for recent purchases
   - Update subscription statuses

3. **Recovery**
   - Fix webhook endpoint issue
   - Replay all missed events from Stripe Dashboard
   - Run reconciliation to ensure data consistency

### Database Corruption
1. **Assessment**
   - Identify scope of corruption
   - Check backups availability
   - Document affected users

2. **Recovery**
   - Restore from most recent backup
   - Replay events from backup timestamp
   - Manual correction for any remaining issues

3. **Validation**
   - Run full reconciliation
   - Test critical payment flows
   - Monitor for additional issues