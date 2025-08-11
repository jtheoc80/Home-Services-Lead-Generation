# Redis Configuration Guide

## Overview

Redis is used for caching, rate limiting, distributed locks, deduplication, and optional queueing in the Home Services Lead Generation platform.

## What Redis is Used For

### 1. Caching
- API response caching
- Database query result caching
- Temporary data storage

### 2. Rate Limiting
- Per-user/IP rate limiting on API endpoints
- Sliding window rate limiting implementation

### 3. Distributed Locks
- Preventing race conditions in concurrent operations
- Ensuring single-instance execution of critical tasks

### 4. Deduplication
- Preventing duplicate permit processing
- Set-based deduplication with TTL

### 5. Queue System (Optional)
- Redis Streams for background job processing
- Feature-flagged with `USE_REDIS_QUEUE`

## Key Prefixes and Patterns

| Prefix | Purpose | Example | TTL |
|--------|---------|---------|-----|
| `cache:*` | General caching | `cache:user:123` | 30-3600s |
| `rate:*` | Rate limiting | `rate:user123:/api/leads` | 60s |
| `lock:*` | Distributed locks | `lock:ingest-permits` | 300s |
| `dedupe:*` | Deduplication sets | `dedupe:permits` | 90 days |
| `queue:*` | Stream queues | `queue:scrape` | Persistent |

## Typical TTLs

- **Cache entries**: 30 seconds to 1 hour
- **Rate limit counters**: 60 seconds (window size)
- **Locks**: 5 minutes (default), configurable
- **Deduplication sets**: 90 days
- **Queue streams**: Persistent until processed

## Environment Configuration

```bash
# Production (TLS-enabled)
REDIS_URL=rediss://default:<password>@<host>:<port>

# Development (local)
REDIS_URL=redis://localhost:6379/0

# Feature flags
USE_REDIS_QUEUE=false  # Enable Redis-based queue processing
```

## Security Notes

- **Server-side only**: Only backend server code directly accesses Redis
- **TLS required**: Use `rediss://` URLs for production connections
- **No frontend access**: Frontend gets Redis status via health API proxy
- **Connection pooling**: Automatic connection management with health checks

## Monitoring

### Health Checks
- Backend `/healthz` endpoint includes Redis connectivity
- Frontend `/api/health` proxies backend health status
- Connection timeout: 300ms

### Key Metrics to Monitor
- Connection status and latency
- Memory usage
- Key count by prefix
- Stream consumer lag (if using queues)

## Provider Setup

### Upstash Redis
```bash
# Get connection URL from Upstash console
REDIS_URL=rediss://default:<password>@<region>-<cluster>.upstash.io:6379
```

### Redis Cloud
```bash
# Get connection URL from Redis Cloud console  
REDIS_URL=rediss://default:<password>@<endpoint>:<port>
```

### Local Development
```bash
# Start Redis locally
docker run -d -p 6379:6379 redis:alpine

# Or via Homebrew on macOS
brew install redis
brew services start redis

REDIS_URL=redis://localhost:6379/0
```

## Testing

Run the smoke test to verify Redis functionality:

```bash
python scripts/redis_smoketest.py
```

This tests:
- Connection and ping
- Cache operations (get/set)
- Distributed locks
- Stream operations (if enabled)

## Troubleshooting

### Connection Issues
1. Verify `REDIS_URL` format and credentials
2. Check network connectivity to Redis host
3. Ensure TLS is used for cloud providers (`rediss://`)

### High Memory Usage
1. Check TTLs are set on all keys
2. Monitor key count by prefix
3. Consider increasing TTLs for frequently accessed data

### Lock Contention
1. Review lock timeout settings
2. Check for stuck locks: `redis-cli KEYS "lock:*"`
3. Manually clear stuck locks if needed