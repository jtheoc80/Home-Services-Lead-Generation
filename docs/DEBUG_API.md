# Debug API Endpoint Documentation

## Overview

The debug API endpoint `/api/leads/trace/[id]` provides detailed tracing information for debugging lead processing issues. This endpoint is protected by a secure API key to prevent unauthorized access to sensitive debugging data.

## Security

This endpoint requires authentication via the `X-Debug-Key` header. The key must match the `DEBUG_API_KEY` environment variable configured on the server.

### Environment Setup

1. **Generate a secure 64-character hex key:**
   ```bash
   node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
   ```

2. **Configure the key in your environment:**
   - **Local development:** Add to `.env` file
   - **Vercel:** Add to Environment Variables in project settings
   - **GitHub Secrets:** Add as repository secret for CI/CD

   ```env
   DEBUG_API_KEY=4fee8941cb95a2d8428538975c181a0adba64dfd15b99c97480b3c653d5855eb
   ```

## API Usage

### Endpoint
```
GET /api/leads/trace/[id]
```

### Headers
- `X-Debug-Key`: Required. Must match the configured `DEBUG_API_KEY`

### Parameters
- `id`: The trace ID to retrieve debugging information for

### Response

#### Success (200)
```json
{
  "trace_id": "example-trace-id",
  "ingest_logs": [
    {
      "id": 1,
      "trace_id": "example-trace-id",
      "stage": "validation",
      "ok": true,
      "message": "Data validation passed",
      "created_at": "2023-12-01T10:00:00Z"
    }
  ],
  "related_leads": [
    {
      "id": "lead-123",
      "name": "John Doe",
      "created_at": "2023-12-01T10:05:00Z"
    }
  ],
  "summary": {
    "total_logs": 5,
    "successful_stages": 4,
    "failed_stages": 1,
    "stages": ["validation", "enrichment", "scoring", "notification"],
    "duration_ms": 245
  }
}
```

#### Unauthorized (401)
```json
{
  "error": "Unauthorized. X-Debug-Key header required."
}
```

#### Server Error (500)
```json
{
  "error": "Debug endpoint not available"
}
```

## curl Examples

### Basic Usage
```bash
curl -X GET \
  "https://your-domain.com/api/leads/trace/your-trace-id" \
  -H "X-Debug-Key: 4fee8941cb95a2d8428538975c181a0adba64dfd15b99c97480b3c653d5855eb"
```

### With Pretty JSON Output
```bash
curl -X GET \
  "https://your-domain.com/api/leads/trace/your-trace-id" \
  -H "X-Debug-Key: 4fee8941cb95a2d8428538975c181a0adba64dfd15b99c97480b3c653d5855eb" \
  -H "Accept: application/json" | jq .
```

### Local Development
```bash
curl -X GET \
  "http://localhost:3000/api/leads/trace/your-trace-id" \
  -H "X-Debug-Key: 4fee8941cb95a2d8428538975c181a0adba64dfd15b99c97480b3c653d5855eb"
```

### Testing Authentication (Should return 401)
```bash
# Without key
curl -X GET "https://your-domain.com/api/leads/trace/test-id"

# With wrong key  
curl -X GET \
  "https://your-domain.com/api/leads/trace/test-id" \
  -H "X-Debug-Key: wrong-key"
```

## Security Features

1. **Header-based Authentication**: Uses `X-Debug-Key` header instead of URL parameters to prevent key leakage in logs
2. **Key Masking**: All debug keys are masked as `[REDACTED]` in server logs
3. **Environment Validation**: Endpoint returns 500 error if `DEBUG_API_KEY` is not configured
4. **Input Validation**: Safely handles special characters and very long keys
5. **No Key Reflection**: Debug keys are never included in API responses

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Verify `X-Debug-Key` header is present
   - Ensure the key matches the server's `DEBUG_API_KEY` exactly
   - Check for extra whitespace or encoding issues

2. **500 Server Error**
   - Ensure `DEBUG_API_KEY` is configured in the server environment
   - Check server logs for configuration issues

3. **404 Not Found**
   - Verify the endpoint URL is correct
   - Ensure the trace ID exists in the system

### Environment Variables

Make sure these environment variables are set:

```env
# Required for debug endpoint
DEBUG_API_KEY=your-64-char-hex-key

# Required for database access
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
```

## Best Practices

1. **Key Management**
   - Generate a new key for each environment (dev, staging, prod)
   - Use a secure random generator for key creation
   - Store keys securely in environment variables, not in code

2. **Access Control**
   - Only share debug keys with authorized developers
   - Rotate keys regularly
   - Remove access when team members leave

3. **Monitoring**
   - Monitor debug endpoint usage in production
   - Set up alerts for unauthorized access attempts
   - Review access logs regularly