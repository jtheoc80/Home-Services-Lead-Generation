# Secured TX Permits Ingestion Setup

This document explains the secured permit ingestion endpoint and GitHub Action scheduler implementation.

## Overview

The `/api/permits/ingest` endpoint is now protected with a shared secret header (`X-Ingest-Key`) and can be triggered automatically via GitHub Actions on a nightly schedule.

## Security Features

- **Header-based Authentication**: Uses `X-Ingest-Key` header instead of URL parameters to prevent key leakage in logs
- **Service Role Access**: Uses `SUPABASE_SERVICE_ROLE_KEY` to bypass RLS for automated ingestion
- **Node Runtime**: Ensures proper runtime configuration for server operations
- **No Caching**: Prevents caching issues with dynamic data ingestion

## Environment Setup

### 1. Generate a Secure API Key

```bash
# Generate a secure 64-character hex key
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 2. Configure Environment Variables

#### Local Development (.env.local)
```env
INGEST_API_KEY=your-generated-64-char-hex-key
```

#### Vercel Deployment
Add to Vercel project environment variables:
- `INGEST_API_KEY` = your-generated-64-char-hex-key

#### GitHub Secrets
Add to repository secrets:
- `INGEST_API_KEY` = your-generated-64-char-hex-key  
- `VERCEL_DOMAIN` = your-app.vercel.app (without https://)

## API Usage

### Endpoint
```
POST /api/permits/ingest
```

### Headers
- `Content-Type: application/json`
- `X-Ingest-Key: <your-api-key>` (Required)

### Request Body
```json
{
  "source": "austin|houston|dallas|all"
}
```

### curl Examples

#### Valid Request
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Ingest-Key: your-api-key" \
  -d '{"source": "all"}' \
  https://your-app.vercel.app/api/permits/ingest
```

#### Expected Response (Success)
```json
{
  "success": true,
  "source": "all",
  "summary": {
    "fetched": 150,
    "processed": 150,
    "inserted": 25,
    "updated": 125,
    "errors": 0
  },
  "diagnostics": {
    "samples": [...],
    "runtime_info": {
      "runtime": "nodejs",
      "service_role_used": true,
      "timestamp": "2024-01-01T12:00:00.000Z"
    }
  }
}
```

## GitHub Action Automation

### Workflow: `ingest-tx-vercel.yml`

**Triggers:**
- **Nightly Schedule**: Every day at 5 AM UTC (11 PM CST)
- **Manual**: Via GitHub Actions UI

**Features:**
- Calls Vercel `/api/permits/ingest` endpoint directly
- Includes authentication via `X-Ingest-Key` header
- Provides detailed summary in workflow output
- Supports manual source selection (austin, houston, dallas, all)

### Manual Execution

1. Go to **Actions** tab in GitHub repository
2. Select **"TX Permits Ingestion (Vercel API)"** workflow
3. Click **"Run workflow"**
4. Select source: `austin`, `houston`, `dallas`, or `all`
5. Click **"Run workflow"** button

## Error Handling

### Authentication Errors

**Missing API Key (500)**
```json
{ "error": "Ingest endpoint not available" }
```

**Invalid API Key (401)**
```json
{ "error": "Unauthorized. X-Ingest-Key header required." }
```

### Data Processing Errors (500)
```json
{
  "error": "Internal server error during permit ingestion",
  "message": "Specific error details"
}
```

## Security Best Practices

1. **Key Management**
   - Generate a new key for each environment (dev, staging, prod)
   - Use a secure random generator for key creation
   - Store keys securely in environment variables, never in code

2. **Access Control**
   - Only share ingest keys with authorized systems
   - Rotate keys regularly
   - Monitor endpoint usage in production

3. **Monitoring**
   - Set up alerts for unauthorized access attempts (401 responses)
   - Review ingest logs regularly
   - Monitor for unusual ingestion patterns

## Testing

Use the provided test script to verify setup:

```bash
# Make script executable
chmod +x test-ingest-security.sh

# Run security tests
./test-ingest-security.sh
```

## Migration from Python Pipeline

The original Python-based pipeline (`ingest-tx.yml`) remains functional. The new Vercel-based approach (`ingest-tx-vercel.yml`) provides:

- **Simpler deployment**: No Python dependencies or database migrations needed
- **Better integration**: Direct API calls to your deployed frontend
- **Unified authentication**: Same service role key used by frontend
- **Real-time monitoring**: Standard HTTP response codes and JSON responses

Choose the approach that best fits your deployment strategy.