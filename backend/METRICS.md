# Prometheus Metrics Implementation

This document describes the Prometheus-style metrics implementation for the Home Services Lead Generation backend.

## Overview

The application now includes comprehensive monitoring with Prometheus-compatible metrics covering HTTP requests, request durations, and data ingestion operations.

## Available Metrics

### HTTP Request Metrics

#### `http_requests_total`
- **Type**: Counter
- **Description**: Total number of HTTP requests
- **Labels**:
  - `method`: HTTP method (GET, POST, PUT, DELETE, etc.)
  - `path`: Request path (normalized to reduce cardinality)
  - `status`: HTTP status code

#### `http_request_duration_seconds`
- **Type**: Histogram
- **Description**: HTTP request duration in seconds
- **Labels**:
  - `method`: HTTP method
  - `path`: Request path (normalized)
- **Buckets**: 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, +Inf

### Data Ingestion Metrics

#### `ingest_rows_total`
- **Type**: Counter
- **Description**: Total number of rows ingested
- **Labels**:
  - `source`: Data source (csv_copy, csv_insert, etc.)
  - `status`: Operation status (success, error)

## Configuration

### Environment Variables

- `ENABLE_METRICS`: Enable/disable metrics collection (default: false)
- `METRICS_USERNAME`: Basic auth username for /metrics endpoint (default: admin)
- `METRICS_PASSWORD`: Basic auth password for /metrics endpoint (default: changeme)

### Production Deployment

For production deployments:

```bash
# Enable metrics
export ENABLE_METRICS=true

# Set secure credentials
export METRICS_USERNAME=your_metrics_user
export METRICS_PASSWORD=your_secure_password
```

## Security

### Authentication

The `/metrics` endpoint is protected by HTTP Basic Authentication. Credentials are configured via environment variables.

### Production Safety

- Metrics are **disabled by default** in all environments
- Must be explicitly enabled with `ENABLE_METRICS=true`
- Uses constant-time password comparison to prevent timing attacks
- Returns 404 when metrics are disabled (instead of revealing the endpoint exists)

## Usage

### Accessing Metrics

```bash
# With curl
curl -u username:password http://localhost:8000/metrics

# Example response (truncated)
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/health",status="200"} 42.0
http_requests_total{method="POST",path="/api/submit",status="201"} 15.0

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.005",method="GET",path="/health"} 35.0
http_request_duration_seconds_sum{method="GET",path="/health"} 1.2345
http_request_duration_seconds_count{method="GET",path="/health"} 42.0
```

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'leadledgerpro-api'
    static_configs:
      - targets: ['your-api-host:8000']
    metrics_path: '/metrics'
    basic_auth:
      username: your_metrics_user
      password: your_secure_password
    scrape_interval: 30s
```

### Grafana Dashboard

Key metrics to monitor:

1. **Request Rate**: `rate(http_requests_total[5m])`
2. **Error Rate**: `rate(http_requests_total{status=~"4..|5.."}[5m])`
3. **Response Time**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))`
4. **Ingestion Rate**: `rate(ingest_rows_total[5m])`

## Path Normalization

To prevent high cardinality issues, paths are automatically normalized:

- UUIDs: `/api/users/550e8400-e29b-41d4-a716-446655440000` → `/api/users/{uuid}`
- Numeric IDs: `/api/users/123` → `/api/users/{id}`
- User IDs: `/api/subscription/status/user-456` → `/api/subscription/status/{user_id}`
- Query parameters are removed

## Development

### Running Tests

```bash
# Run all metrics tests
python -m pytest tests/test_metrics.py -v

# Run middleware integration tests
python -m pytest tests/test_middleware_simple.py -v

# Run demonstration
python /tmp/metrics_demo.py
```

### Adding New Metrics

1. Define metrics in `app/metrics.py`
2. Add tracking calls where appropriate
3. Update tests
4. Update documentation

Example:

```python
from app.metrics import track_ingestion

# In your data processing code
try:
    rows_processed = process_data(data)
    track_ingestion("api_upload", rows_processed, "success")
except Exception as e:
    track_ingestion("api_upload", 0, "error")
    raise
```

## Troubleshooting

### Metrics Not Appearing

1. Check `ENABLE_METRICS=true` is set
2. Verify credentials are correct
3. Check application logs for errors
4. Ensure requests are actually being made to tracked endpoints

### High Memory Usage

If you notice high memory usage:

1. Check for high cardinality labels (especially paths)
2. Review path normalization rules
3. Consider adjusting histogram buckets
4. Monitor metrics collection frequency

### Performance Impact

The metrics collection has minimal performance impact:

- Counters: ~50ns per increment
- Histograms: ~200ns per observation
- Path normalization: ~1-2μs per request

For high-traffic applications (>1000 RPS), consider:

- Reducing histogram bucket count
- Sampling metrics collection
- Using separate metrics collection process