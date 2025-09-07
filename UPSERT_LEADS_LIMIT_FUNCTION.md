# upsert_leads_from_permits_limit() RPC Function

## Overview

This document describes the `upsert_leads_from_permits_limit()` RPC function that extends the existing `upsert_leads_from_permits()` function with a limit parameter for controlled batch processing of leads from permits data.

## Problem Addressed

The workflow in the problem statement requires calling:
```bash
curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"p_limit":50,"p_days":365}'
```

However, the `upsert_leads_from_permits_limit` function did not exist. This implementation creates that function with the exact parameters needed.

## Solution

The new function extends the existing `upsert_leads_from_permits()` function with:

### Key Features

1. **Limit Parameter**: `p_limit` parameter to control batch size (up to 50 in the problem statement)
2. **Date Filtering**: `p_days` parameter to filter permits from the last N days (365 in the problem statement)
3. **Correct Column Usage**: Uses `public.permits.issued_date` (NOT `issue_date`)
4. **Comprehensive Lead Creation**: Creates leads from permits data with proper field mapping
5. **Conflict Handling**: Handles existing leads with UPDATE on conflict
6. **Return Values**: Returns counts of inserted, updated, and total processed records

### Function Signature

```sql
CREATE OR REPLACE FUNCTION public.upsert_leads_from_permits_limit(
  p_limit INTEGER DEFAULT NULL,
  p_days INTEGER DEFAULT NULL
)
RETURNS TABLE(
  inserted_count INTEGER,
  updated_count INTEGER,
  total_processed INTEGER
)
```

**Parameters:**
- `p_limit` (optional): Maximum number of permits to process. If NULL, processes all matching permits.
- `p_days` (optional): Filter permits to only those from the last N days. If NULL, processes permits from all time.

**Returns:**
- `inserted_count`: Number of new leads created
- `updated_count`: Number of existing leads updated  
- `total_processed`: Total number of leads processed

### Column Mapping

The function maps permit data to lead data as follows:

| Permits Column | Leads Column | Notes |
|----------------|--------------|-------|
| `id` | `permit_id` | UUID foreign key |
| `permit_id` | `external_permit_id` | Canonical permit identifier |
| `work_description` | `name` | Lead name (with fallback) |
| `address` | `address` | Property address |
| `city` | `city` | Property city |
| `county` | `county` | Property county |
| `permit_type/permit_class` | `service/trade` | Service categorization |
| `status` | `status` | Lead status (defaults to 'new') |
| `valuation` | `value` | Property/project value |
| **`issued_date`** | `created_at` | **Correct date column usage** |

## Usage

### Running the Migration

1. Apply the migration file:
   ```bash
   make db-migrate
   ```
   Or manually:
   ```sql
   -- Run in Supabase SQL Editor or psql
   \i supabase/migrations/20250121000000_add_upsert_leads_from_permits_limit.sql
   ```

2. Call the function:
   ```sql
   -- Process up to 50 permits from last 365 days (problem statement)
   SELECT * FROM public.upsert_leads_from_permits_limit(50, 365);
   
   -- Process up to 10 permits from last 7 days
   SELECT * FROM public.upsert_leads_from_permits_limit(10, 7);
   
   -- Process all permits from last 30 days
   SELECT * FROM public.upsert_leads_from_permits_limit(NULL, 30);
   
   -- Process up to 100 permits from all time
   SELECT * FROM public.upsert_leads_from_permits_limit(100, NULL);
   ```

### HTTP RPC Usage

Via Supabase REST API (as used in workflows):
```bash
# Problem statement parameters
curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"p_limit":50,"p_days":365}'

# Other examples
curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"p_limit":10,"p_days":7}'
```

### Testing

Run the comprehensive test script to verify functionality:
```sql
-- Run in Supabase SQL Editor or psql
\i test_upsert_leads_from_permits_limit.sql
```

The test script validates:
- Function exists and can be called
- Limit parameter works correctly
- Days parameter filters correctly
- Problem statement parameters (p_limit=50, p_days=365) work
- Correct date column usage (issued_date, not issue_date)
- Proper lead creation and conflict handling

## Files Created

1. `supabase/migrations/20250121000000_add_upsert_leads_from_permits_limit.sql` - The migration file
2. `test_upsert_leads_from_permits_limit.sql` - Comprehensive test script
3. `UPSERT_LEADS_LIMIT_FUNCTION.md` - This documentation file

## Implementation Notes

- The function follows existing code patterns from the original `upsert_leads_from_permits()` function
- Uses proper PostgreSQL best practices for upsert operations with LIMIT
- Includes comprehensive error handling and data validation
- Designed to be safe for repeated execution (idempotent)
- Orders results by date (most recent first) when applying limits

## Relationship to Existing Functions

This function complements the existing `upsert_leads_from_permits()` function:

- **Original function**: `upsert_leads_from_permits(p_days)` - Processes all permits within date range
- **New function**: `upsert_leads_from_permits_limit(p_limit, p_days)` - Adds batch size control with limit parameter

Both functions can be used together depending on the use case:
- Use the original for full processing
- Use the new function for testing, controlled batches, or live demonstrations

## Verification Checklist

- [x] Function created with correct signature (p_limit, p_days parameters)
- [x] Function uses `public.permits.issued_date` (NOT `issue_date`)
- [x] Proper field mapping between permits and leads tables
- [x] Conflict resolution with ON CONFLICT DO UPDATE
- [x] Return values for monitoring and logging
- [x] Limit parameter functionality implemented
- [x] Comprehensive test coverage for all parameters
- [x] Documentation provided
- [x] Problem statement parameters (p_limit=50, p_days=365) validated

The implementation successfully addresses the problem statement by providing the exact RPC function with the required parameters that can be called from the workflow.