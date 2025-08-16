# Supabase Schema Alignment Migration Guide

## Overview

This document describes the comprehensive Supabase schema alignment migration that standardizes identifiers, adds missing fields, and creates a robust permit→lead pipeline.

## Migration File

**Location**: `supabase/migrations/align_repo_supabase.sql`

## Goals Achieved

✅ **Standardized Identifiers**: Canonical `permit_id` (text) with `(source, permit_id)` uniqueness  
✅ **Backward Compatibility**: Existing UUID `permits.id` and `leads.permit_id` (UUID FK) still work  
✅ **Enhanced Schema**: Added missing fields (`applicant`, `owner`, `contractor_name`, `work_class`, `provenance`, `finaled_at`)  
✅ **Normalized Naming**: Compatibility views for old column names  
✅ **Enhanced RPC**: `upsert_permit(jsonb)` now derives `permit_id` from payload  
✅ **Robust Pipeline**: AFTER INSERT trigger creates leads with consistent fields  
✅ **Safe Indexing**: Proper indexes and optional PostGIS support  

## Schema Changes

### Permits Table Enhancements

```sql
-- New columns added
ALTER TABLE public.permits ADD COLUMN permit_id TEXT;          -- Canonical identifier
ALTER TABLE public.permits ADD COLUMN applicant TEXT;          -- Normalized applicant
ALTER TABLE public.permits ADD COLUMN owner TEXT;              -- Normalized owner  
ALTER TABLE public.permits ADD COLUMN work_class TEXT;         -- Work classification
ALTER TABLE public.permits ADD COLUMN provenance JSONB;        -- Data lineage
ALTER TABLE public.permits ADD COLUMN finaled_at TIMESTAMPTZ;  -- Completion timestamp

-- New unique constraint (partial)
CREATE UNIQUE INDEX uq_permits_source_permit_id 
ON public.permits(source, permit_id) 
WHERE permit_id IS NOT NULL;
```

### Leads Table Enhancements

```sql
-- Service/trade synchronization
ALTER TABLE public.leads ADD COLUMN service TEXT;  -- Service category
ALTER TABLE public.leads ADD COLUMN trade TEXT;    -- Trade classification
```

### Compatibility Views

```sql
-- permits_compat: Column aliases for backward compatibility
-- issue_date → issued_date
-- valuation → value  
-- postal_code → zipcode

-- leads_compat: Trade/service compatibility
-- Exposes both service and trade with fallback logic
```

## Function Enhancements

### Enhanced upsert_permit() RPC

```sql
CREATE OR REPLACE FUNCTION public.upsert_permit(p JSONB)
```

**New Features**:
- Derives `permit_id` from payload: `permit_id` → `permit_no` → `source_record_id`
- Handles both `valuation` and `value` fields from payload
- Updates both normalized fields (`applicant`, `owner`) and legacy fields
- Sets `updated_at = NOW()` and `created_at` defaults

### Enhanced create_lead_from_permit() Function

**Improvements**:
- Uses canonical `permit_id` (prefers text permit_id over UUID)
- Enhanced field mapping: `applicant` → `owner` → `contractor_name` → 'Unknown'
- Improved service categorization including `work_class`
- Syncs both `service` and `trade` columns
- Enriched metadata with canonical identifiers

## Testing

### Test Suite

Run the comprehensive test suite:

```bash
npm run test:schema:alignment
```

**Test Coverage**:
1. ✅ Enhanced permits table schema validation
2. ✅ Leads service/trade column verification  
3. ✅ Compatibility views accessibility
4. ✅ Enhanced upsert_permit() RPC with sentinel data
5. ✅ Permit→lead pipeline with canonical permit_id
6. ✅ Unique constraint verification

### Sentinel Test Case

The migration includes a test case exactly as specified:

```sql
SELECT public.upsert_permit(jsonb_build_object(
  'source','selftest','source_record_id','sent-1','permit_no','SENT-1',
  'permit_id','SENT-1','jurisdiction','Austin','county','Travis',
  'status','Issued','address','100 Test St','city','Austin','state','TX',
  'issued_date', now()::timestamptz, 'value', 12345
));
```

## Deployment Instructions

### 1. Execute Migration

Run the migration in Supabase SQL editor as the `postgres` (Owner) user:

```sql
-- Copy and paste the entire contents of:
-- supabase/migrations/align_repo_supabase.sql
```

### 2. Verify Installation

```sql
-- Check permits enhancements
SELECT permit_id, applicant, owner, work_class FROM public.permits LIMIT 5;

-- Check leads service/trade sync
SELECT service, trade FROM public.leads WHERE permit_id IS NOT NULL LIMIT 5;

-- Test compatibility views
SELECT issue_date, value, postal_code FROM public.permits_compat LIMIT 5;
```

### 3. Test Sentinel Case

```sql
-- Should work without errors
SELECT public.upsert_permit(jsonb_build_object(
  'source','selftest','source_record_id','sent-1','permit_no','SENT-1',
  'permit_id','SENT-1','jurisdiction','Austin','county','Travis',
  'status','Issued','address','100 Test St','city','Austin','state','TX',
  'issued_date', now()::timestamptz, 'value', 12345
));
```

## Backward Compatibility

### Existing Code Compatibility

✅ **Existing permit ingestion**: Works unchanged  
✅ **UUID-based permit_id references**: Still functional  
✅ **Current upsert_permit() calls**: Enhanced with new features  
✅ **Lead creation triggers**: Improved with canonical identifiers  

### Legacy Column Support

The compatibility views ensure existing code continues to work:

```sql
-- Old query style still works
SELECT issue_date, value, postal_code FROM permits_compat;

-- New query style available  
SELECT issued_date, valuation, zipcode FROM permits;
```

## Performance Considerations

### New Indexes

```sql
-- Canonical permit_id lookup
CREATE INDEX idx_permits_permit_id ON public.permits(permit_id);

-- Enhanced search capabilities
CREATE INDEX idx_permits_applicant ON public.permits(applicant);
CREATE INDEX idx_permits_owner ON public.permits(owner); 
CREATE INDEX idx_permits_work_class ON public.permits(work_class);
CREATE INDEX idx_permits_finaled_at ON public.permits(finaled_at);
```

### Query Optimization

- Partial unique index only applies when `permit_id IS NOT NULL`
- Maintains existing `(source, source_record_id)` uniqueness
- Optimized compatibility views with direct column mapping

## Migration Validation

After running the migration, the following should be true:

1. ✅ All existing permits have `permit_id` populated
2. ✅ New permits get canonical `permit_id` from payload  
3. ✅ Leads have both `service` and `trade` columns synced
4. ✅ Compatibility views provide expected column aliases
5. ✅ Enhanced upsert_permit() handles all field mappings
6. ✅ Permit→lead pipeline uses canonical identifiers
7. ✅ Unique constraints prevent duplicate permits per source

## Troubleshooting

### Common Issues

1. **Migration fails on unique constraint**: Check for existing duplicate (source, permit_id) combinations
2. **Compatibility views not found**: Ensure migration completed successfully
3. **upsert_permit() not working**: Verify function was replaced successfully
4. **Test failures**: Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables

### Validation Queries

```sql
-- Check migration completion
SELECT 
  COUNT(*) as total_permits,
  COUNT(permit_id) as permits_with_canonical_id,
  COUNT(DISTINCT CONCAT(source, ':', permit_id)) as unique_source_permit_combinations
FROM public.permits;

-- Verify leads pipeline
SELECT 
  source,
  COUNT(*) as count,
  COUNT(DISTINCT service) as unique_services
FROM public.leads 
WHERE permit_id IS NOT NULL
GROUP BY source;
```

## Support

For issues with the migration:

1. Check the test suite output: `npm run test:schema:alignment`
2. Verify environment variables are set correctly
3. Ensure migration was run as postgres (Owner) user
4. Check Supabase logs for any constraint violations