# E2E Supabase Delta Testing

This document describes the new E2E Supabase delta testing functionality implemented to validate ETL pipeline data integrity.

## Overview

The `scripts/e2e_supabase_delta.ts` script was added to provide comprehensive validation of the Supabase database state after ETL operations. This complements the existing E2E smoke tests by focusing on data layer validation.

## Features

### 1. Database Connectivity Test
- Verifies connection to Supabase using service role credentials
- Tests basic table access permissions
- Validates RLS (Row Level Security) configurations

### 2. Data Freshness Validation
- Configurable threshold for recent data (default: 24 hours)
- Counts records within the threshold period
- Reports age of the most recent record

### 3. Data Integrity Checks
- Validates required fields are populated
- Checks data quality metrics (valid IDs, dates, addresses)
- Provides quality scoring (requires ≥70% quality)

### 4. Query Performance Testing  
- Tests indexed query performance
- Validates response times (threshold: 5 seconds)
- Ensures database is responsive under load

### 5. Schema Compliance Verification
- Validates expected table columns exist
- Tests column accessibility and types
- Ensures schema matches expectations

## Usage

### Manual Testing
```bash
# Test with default 24-hour threshold
npm run e2e:supabase

# Test with custom threshold
tsx scripts/e2e_supabase_delta.ts --threshold-hours 12
```

### CI/CD Integration
The script is automatically run as part of the E2E workflow on successful deployments:

```yaml
- name: Run Supabase delta test
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  run: |
    tsx scripts/e2e_supabase_delta.ts --threshold-hours 24
```

## Environment Variables

- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key for database access

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed
- `2` - Script error or configuration issue

## Test Results

The script provides detailed output including:
- Individual test results with pass/fail status
- Performance metrics and timing data
- Data quality scores and statistics
- Error details for debugging

Results are uploaded as GitHub Actions artifacts and included in PR comments for visibility.