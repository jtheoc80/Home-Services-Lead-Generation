# Environment Variables Configuration

This document describes the new environment variables that control export permissions, caching, and notification features in the Home Services Lead Generation application.

## Required Environment Variables

### Export Control
- **`ALLOW_EXPORTS`**: Controls whether data exports are permitted
  - Values: `true`, `false` (default: `false`)
  - When `false`, all export requests will be blocked with appropriate logging and notifications
  - Example: `ALLOW_EXPORTS=true`

### Redis Caching
- **`REDIS_URL`**: Connection URL for Redis cache server
  - Format: `redis://host:port/database`
  - Used for caching lead scores, export results, and rate limiting
  - Example: `REDIS_URL=redis://localhost:6379/0`

### Email Notifications (SendGrid)
- **`SENDGRID_API_KEY`**: API key for SendGrid email service
  - Used for sending email notifications about export requests and lead processing
  - Example: `SENDGRID_API_KEY=SG.your_api_key_here`

### SMS Notifications (Twilio)
- **`TWILIO_SID`**: Twilio Account SID
- **`TWILIO_TOKEN`**: Twilio Auth Token  
- **`TWILIO_FROM`**: Phone number to send SMS from (E.164 format)
  - Used for sending SMS notifications about system events
  - Example:
    ```
    TWILIO_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    TWILIO_TOKEN=your_auth_token_here
    TWILIO_FROM=+1234567890
    ```

### GitHub Actions Ingest Agents
- **`INGEST_URL`**: Vercel endpoint for permit data ingestion
  - Format: `https://your-app.vercel.app/api/permits/ingest`
  - Used by the ingest-agents workflow for Austin/Dallas data ingestion
  - Example: `INGEST_URL=https://leads-app.vercel.app/api/permits/ingest`

- **`DEBUG_URL`**: Vercel endpoint for database status checking  
  - Format: `https://your-app.vercel.app/api/_debug/sb`
  - Returns Supabase leads and permits counts for verification
  - Example: `DEBUG_URL=https://leads-app.vercel.app/api/_debug/sb`

- **`CRON_SECRET`**: Authentication secret for secured Vercel endpoints
  - Used in x-cron-secret header to protect ingest/debug endpoints
  - Should match the secret configured in Vercel for API route protection
  - Example: `CRON_SECRET=your_secure_random_string_here`

### Webhook Security
- **`WEBHOOK_SECRET`**: General webhook authentication secret
  - Used for authenticating webhook requests to your application
  - Should be a 32+ character random string generated with: `openssl rand -hex 32`
  - Example: `WEBHOOK_SECRET=6b62cc6f1dedc79d2bd950732c2cabb1d9a89b2c927c23bdfb73954808e784dc`

## Configuration Files

Add these variables to your environment configuration files:

### Root `.env`
```bash
# Export Control
ALLOW_EXPORTS=false

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Email Notifications (SendGrid)
SENDGRID_API_KEY=your_sendgrid_api_key_here

# SMS Notifications (Twilio)
TWILIO_SID=your_twilio_account_sid_here
TWILIO_TOKEN=your_twilio_auth_token_here
TWILIO_FROM=+1xxxxxxxxxx
```

### GitHub Actions Secrets

Configure these secrets in **GitHub → Settings → Secrets and variables → Actions**:

```bash
# Ingest Agents Workflow
INGEST_URL=https://your-app.vercel.app/api/permits/ingest
DEBUG_URL=https://your-app.vercel.app/api/_debug/sb  
CRON_SECRET=your_secure_random_string_here
```

### Backend `.env`
```bash
# (Same variables as above, plus backend-specific settings)
```

### Frontend `.env`
```bash
# (Same variables as above, plus frontend-specific settings)
```

### Permit Leads `.env`
```bash
# (Same variables as above, plus permit leads-specific settings)
```

## Required Dependencies

To enable full functionality, install the following optional dependencies:

### For Redis Caching
```bash
pip install redis>=4.0.0
```

### For Email Notifications
```bash
pip install sendgrid>=6.0.0
```

### For SMS Notifications
```bash
pip install twilio>=7.0.0
```

## Feature Behavior

### When Environment Variables Are Not Set
- **Export Control**: Exports are disabled by default (secure by default)
- **Caching**: All cache operations return safely without errors
- **Notifications**: Notification attempts are logged but not sent

### When Environment Variables Are Set But Libraries Are Missing
- **Export Control**: Works normally (no external dependencies)
- **Caching**: Cache operations fail gracefully with warning logs
- **Notifications**: Notification attempts fail gracefully with warning logs

### When Fully Configured
- **Export Control**: Respects `ALLOW_EXPORTS` setting with full logging and notifications
- **Caching**: Lead scores, export results, and rate limiting are cached
- **Notifications**: Email and SMS notifications are sent for system events

## API Endpoints

### Export Data API
- **Endpoint**: `POST /api/export-data`
- **Behavior**: Checks `ALLOW_EXPORTS` environment variable
- **Response**: Returns 403 error when exports are disabled
- **Notifications**: Sends alerts to administrators when export requests are blocked

### Score Leads API (Enhanced)
- **Endpoint**: `POST /api/score-leads`
- **Caching**: Results cached in Redis when available
- **Notifications**: Can send notifications about lead processing completion

## Testing

Run the test suite to verify environment variable functionality:

```bash
cd backend
python -m pytest tests/test_env_vars.py -v
```

Run the demonstration script to see all features in action:

```bash
cd backend
python demo_env_vars.py
```

Run with environment variables set:

```bash
cd backend
ALLOW_EXPORTS=true \
REDIS_URL=redis://localhost:6379/0 \
SENDGRID_API_KEY=test_key \
TWILIO_SID=test_sid \
TWILIO_TOKEN=test_token \
TWILIO_FROM=+1234567890 \
python demo_env_vars.py
```

## Security Considerations

1. **Export Control**: Exports are disabled by default for security
2. **API Keys**: Sensitive environment variables are masked in logs
3. **Graceful Degradation**: Missing services don't cause application failures
4. **Audit Logging**: All export attempts are logged for security auditing
5. **Rate Limiting**: Redis-based rate limiting helps prevent abuse

## Monitoring and Logging

- Export attempts (allowed and blocked) are logged for audit purposes
- Failed notification attempts are logged with warning level
- Cache operations log debug information when enabled
- Rate limiting counters are tracked when Redis is available

## Production Deployment

1. Set `ALLOW_EXPORTS=true` only when data exports are required
2. Configure Redis URL to point to production Redis instance
3. Set valid SendGrid API key for email notifications
4. Configure Twilio credentials for SMS notifications
5. Set `ADMIN_NOTIFICATION_EMAILS` for export request notifications
6. Monitor logs for blocked export attempts and failed notifications