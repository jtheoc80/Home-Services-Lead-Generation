# County NULL Fix Implementation

This directory contains the implementation to fix NULL values in the `public.leads.county` column and enhance the `upsert_leads_from_permits()` function as specified in the problem statement.

## Problem Statement

> Add a default on public.leads.county ('Unknown') and recreate public.upsert_leads_from_permits() so it always supplies county using coalesce(county, inferred-from-jurisdiction, 'Unknown') and a non-null name. Then run the RPC and verify there are no NULLs in county/name and keys are present.

## Solution Overview

### 1. Database Changes

- **Added DEFAULT 'Unknown'** to `public.leads.county` column
- **Updated existing NULL counties** to 'Unknown'
- **Created jurisdiction mapping function** `infer_county_from_jurisdiction()`
- **Enhanced upsert function** with proper county inference logic

### 2. Key Features

- **County Inference**: Maps jurisdiction slugs to county names (tx-harris → Harris County, etc.)
- **Fallback Logic**: Uses `COALESCE(county, inferred-from-jurisdiction, 'Unknown')` 
- **Name Enhancement**: Ensures name is never NULL with improved fallback logic
- **Data Quality**: Guarantees no NULL values in critical fields

## Files

### Migration
- `supabase/migrations/20250107000000_fix_county_nulls.sql` - Main migration script

### Testing & Verification
- `test_county_fix.sql` - Comprehensive test suite for database validation
- `verify_county_fix.sql` - Simple verification script for production use
- `test_county_logic.py` - Logic validation without database
- `demo_county_fix_verification.py` - Demonstration of verification process

## Usage

### 1. Apply the Migration

```bash
# Using psql directly
psql "$DATABASE_URL" -f supabase/migrations/20250107000000_fix_county_nulls.sql

# Or using Supabase CLI
supabase db push
```

### 2. Test the Implementation

```bash
# Run comprehensive tests
psql "$DATABASE_URL" -f test_county_fix.sql

# Or just verify the fix
psql "$DATABASE_URL" -f verify_county_fix.sql
```

### 3. Run the RPC Function

```sql
-- Call the enhanced function
SELECT * FROM public.upsert_leads_from_permits();

-- Or with time filter (last 7 days)
SELECT * FROM public.upsert_leads_from_permits(7);
```

### 4. Verify Results

```sql
-- Check for NULL county values (should be 0)
SELECT COUNT(*) FROM public.leads WHERE county IS NULL;

-- Check for NULL name values (should be 0)  
SELECT COUNT(*) FROM public.leads WHERE name IS NULL;

-- Check for missing keys (should be 0)
SELECT COUNT(*) FROM public.leads WHERE permit_id IS NULL;

-- View county distribution
SELECT county, COUNT(*) as count 
FROM public.leads 
GROUP BY county 
ORDER BY count DESC;
```

## Logic Details

### County Inference

The enhanced function uses this logic for county values:

```sql
COALESCE(
  NULLIF(TRIM(p.county),''),                           -- Use existing county if not empty
  public.infer_county_from_jurisdiction(p.jurisdiction), -- Infer from jurisdiction
  public.infer_county_from_jurisdiction(p.source),       -- Fallback: try source field
  'Unknown'                                             -- Final fallback
)
```

### Jurisdiction Mapping

| Jurisdiction Slug | County Name |
|-------------------|-------------|
| tx-harris | Harris County |
| tx-fort-bend | Fort Bend County |
| tx-brazoria | Brazoria County |
| tx-galveston | Galveston County |
| tx-dallas | Dallas County |
| tx-travis | Travis County |
| tx-bexar | Bexar County |

### Name Enhancement

The enhanced function ensures name is never NULL:

```sql
COALESCE(
  NULLIF(TRIM(p.work_description),''),    -- Use work description if available
  NULLIF(TRIM(p.permit_type),''),         -- Fallback to permit type
  'Permit ' || COALESCE(                  -- Generate permit name
    NULLIF(TRIM(p.permit_number),''),
    NULLIF(TRIM(p.permit_id),''),
    p.id::text,
    '(no #)'
  )
)
```

## Expected Results

After applying the fix:

- ✅ **Zero NULL county values** - all records have county or 'Unknown'
- ✅ **Zero NULL name values** - all records have meaningful names
- ✅ **All records have keys** - permit_id is always present
- ✅ **County inference working** - jurisdictions mapped to counties
- ✅ **Data quality improved** - consistent, reliable lead data

## Testing Without Database

You can test the logic without a database:

```bash
python3 test_county_logic.py
python3 demo_county_fix_verification.py
```

## Rollback

If needed, the changes can be rolled back:

```sql
-- Remove the default
ALTER TABLE public.leads ALTER COLUMN county DROP DEFAULT;

-- Restore original function (see original migration file)
-- Note: You may want to backup data before rollback
```