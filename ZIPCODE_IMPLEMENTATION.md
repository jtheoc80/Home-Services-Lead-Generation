# Zipcode Backfill Implementation Summary

This implementation addresses the requirements to add SQL backfill for updating leads.zipcode from permits, ensure zipcode handling is properly configured, and verify the GitHub Action calls the upsert function.

## Changes Made

### 1. SQL Backfill Script (`sql/backfill_leads_zipcode.sql`)
- Updates `leads.zip` from `permits.zipcode` where zip is currently NULL or empty
- Provides reporting on backfill results
- Includes verification query showing sample updated leads

### 2. Updated upsert_leads_from_permits Function (`supabase/migrations/20250121000000_update_upsert_leads_zipcode.sql`)
- Added `zip` field to the INSERT statement column list
- Maps `permits.zipcode` to `leads.zip` using `NULLIF(p.zipcode,'')` 
- Includes `zip = EXCLUDED.zip` in the ON CONFLICT UPDATE clause
- Updated function documentation

### 3. Fixed create_lead_from_permit Function (`supabase/migrations/20250122000000_fix_create_lead_zipcode.sql`)
- Added detection of `zip` column in leads table (`has_zip_column_in_leads`)
- Added `zip` field to the INSERT statement column list
- Maps `permits.zipcode` to `leads.zip` in the INSERT VALUES
- Handles optional column presence gracefully

### 4. Verification Queries (`sql/verify_leads_zipcode.sql`)
- Shows newest 20 leads with zipcode status (MATCH, MISMATCH, MISSING, etc.)
- Provides summary statistics of zipcode coverage
- Shows daily leads creation with zipcode coverage percentage

### 5. Comprehensive Test Script (`sql/test_zipcode_functionality.sql`)
- Tests backfill functionality
- Tests trigger function with zipcode data
- Tests RPC function with zipcode mapping
- Provides effectiveness summary

## Verification

### GitHub Action Confirmation
The GitHub Action workflow `ingest-tx.yml` already calls `upsert_leads_from_permits` in the "Build leads from fresh permits" step:
```bash
curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"p_days": 7}'
```

### Zipcode Constraint Status
- The `leads.zip` field is TEXT with no NOT NULL constraint (no changes needed)
- The `permits.zipcode` field is TEXT with no NOT NULL constraint
- No default value is needed as the field is already nullable

## Usage

### Run Backfill
```sql
\i sql/backfill_leads_zipcode.sql
```

### Run Verification
```sql
\i sql/verify_leads_zipcode.sql
```

### Test All Functionality
```sql
\i sql/test_zipcode_functionality.sql
```

## Expected Results

After applying these changes:
1. Existing leads will have their zip field populated from corresponding permits
2. New permits will automatically create leads with zipcode via trigger
3. The RPC function will properly map zipcode when creating/updating leads from permits
4. The GitHub Action will continue to work as before but now with proper zipcode handling

## Files Modified/Created

- `sql/backfill_leads_zipcode.sql` (new)
- `sql/verify_leads_zipcode.sql` (new)  
- `sql/test_zipcode_functionality.sql` (new)
- `supabase/migrations/20250121000000_update_upsert_leads_zipcode.sql` (new)
- `supabase/migrations/20250122000000_fix_create_lead_zipcode.sql` (new)