# Redis Chaos Testing Documentation

## Overview

The Redis chaos testing infrastructure validates that the application gracefully handles Redis provider slowness and latency issues. This ensures the system remains responsive and doesn't hang when Redis operations are delayed.

## Features

### Chaos Testing Capabilities

- **Latency Injection**: Simulates 250-500ms delays in Redis operations
- **Timeout Enforcement**: Ensures no operation hangs longer than 1 second
- **Graceful Degradation**: Validates fallback behavior when Redis is slow
- **Comprehensive Coverage**: Tests all major Redis operations (ping, cache, locks, streams, rate limiting)

### Test Categories

1. **Basic Chaos Tests**: Individual Redis operations with injected latency
2. **Timeout Enforcement**: Strict validation that operations complete within 1s
3. **Graceful Degradation**: Verification of fallback behaviors and retry logic

## Usage

### Running Tests

```bash
# Standard Redis smoke test only
npm run redis:smoke

# Chaos testing only
npm run redis:chaos

# Combined standard and chaos testing
npm run redis:smoke:all

# Direct script execution
python scripts/redis_smoketest.py --chaos
python scripts/redis_chaos_smoketest.py
```

### Command Line Options

```bash
# Standard smoke test
python scripts/redis_smoketest.py

# Include chaos testing
python scripts/redis_smoketest.py --chaos
```

## Test Scenarios

### 1. Latency Injection Tests

Tests Redis operations with 250-500ms artificial latency:

- `ping_ms()` - Connection health checks
- `cache_get()` / `cache_setex()` - Caching operations
- `rate_limit()` - Rate limiting with pipeline operations
- `with_lock()` - Distributed lock acquisition/release
- `stream_xadd()` / `stream_readgroup()` - Stream operations

### 2. Timeout Enforcement Tests

Validates that operations absolutely do not exceed 1s:

```python
# Example assertion
if elapsed > 1.0:
    raise Exception(f"Operation hung for {elapsed:.3f}s, exceeding 1s limit")
```

### 3. Graceful Degradation Tests

Verifies fallback behavior:

- Rate limiting defaults to "allow" when Redis is slow
- Locks provide appropriate fallback behavior
- Cache operations handle timeouts gracefully
- No operation causes the application to hang

## Implementation Details

### Chaos Injection Method

The system uses a `ChaosRedisWrapper` that intercepts Redis operations and injects configurable latency:

```python
class ChaosRedisWrapper:
    async def _inject_latency(self):
        """Inject random latency between 250-500ms"""
        delay = random.uniform(0.25, 0.5)
        await asyncio.sleep(delay)
```

### Mock Redis for Testing

When no Redis instance is available, the system uses comprehensive mocks:

```python
# Mock Redis with realistic behavior
mock_redis = AsyncMock()
mock_redis.ping.return_value = True
# ... other operations
```

### Timeout Configuration

All operations are wrapped with strict timeouts:

```python
await asyncio.wait_for(operation, timeout=1.0)
```

## Existing Redis Client Timeouts

The production Redis client already has conservative timeout settings:

```python
Redis.from_url(
    REDIS_URL, 
    socket_timeout=0.3,           # 300ms socket timeout
    socket_connect_timeout=0.3,   # 300ms connection timeout
    # ...
)
```

## Integration with CI/CD

The chaos tests can be integrated into continuous integration:

```yaml
# Example GitHub Actions step
- name: Run Redis Chaos Tests
  run: npm run redis:chaos
```

## Expected Results

### Successful Test Output

```
🔥 Redis Chaos Smoke Test
==================================================
Injecting 250-500ms latency to simulate provider slowness...

Testing ping with chaos latency...
  ✅ PING timed out gracefully: 0.302s

Testing cache operations with chaos latency...
  SETEX completed in 0.422s: True
  GET completed in 0.337s: None

Testing rate limit with chaos latency...
  ✅ RATE_LIMIT completed in 0.346s: True

...

==================================================
Tests: 6 passed, 0 failed
✅ All chaos tests passed - Redis degrades gracefully under latency!
```

### Key Metrics Validated

- **No hangs > 1s**: All operations complete or timeout within 1 second
- **Graceful degradation**: Operations provide appropriate fallbacks
- **Latency tolerance**: System handles 250-500ms Redis delays appropriately
- **Timeout compliance**: Operations respect configured timeout values

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure Python path includes backend directory
2. **Missing Dependencies**: Install `redis[async]` and `pytest-asyncio`
3. **Timeout Failures**: Check if operations are genuinely hanging vs. expected slow behavior

### Debug Mode

Run tests with verbose output:

```bash
python scripts/redis_chaos_smoketest.py 2>&1 | tee chaos_test_output.log
```

## Future Enhancements

Potential improvements for chaos testing:

1. **Variable Latency Ranges**: Configurable latency injection (e.g., 100ms-2s)
2. **Intermittent Failures**: Simulate Redis connection drops
3. **Memory Pressure**: Test behavior under Redis memory constraints
4. **Network Partitions**: Simulate network connectivity issues
5. **Load Testing**: Combine chaos with high request volumes

## Conclusion

This chaos testing infrastructure ensures the Home Services Lead Generation platform remains resilient to Redis provider issues, maintaining system availability and preventing user-facing hangs or timeouts.