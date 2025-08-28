# Supabase Setup Guide

This guide covers setting up the complete permits → leads pipeline infrastructure in your Supabase project.

## Overview

The Home Services Lead Generation platform uses Supabase as its primary database and backend infrastructure. The bootstrap SQL script creates:

- **Permits table**: Stores building permits from various Texas jurisdictions
- **Leads table**: Auto-generated leads from permit data with enrichment
- **Trigger pipeline**: Automatic lead creation with permit ID canonicalization
- **RLS policies**: Secure access controls for anonymous and authenticated users
- **Unique indexes**: Prevent duplicate permits and leads

## Required Environment Variables

Before running the migration, ensure these environment variables are set:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### Where to Find These Values

1. **SUPABASE_URL**: Found in your Supabase project dashboard under Settings → API
2. **SUPABASE_SERVICE_ROLE_KEY**: Found in the same location under "Project API keys" (service_role key)

⚠️ **Security Note**: The service role key has full database access. Never expose it in client-side code or commit it to version control.

## Migration Instructions

### Option 1: Using Supabase CLI (Recommended)

If you have the Supabase CLI installed and configured:

```bash
# Navigate to project root
cd your-project-directory

# Push the migration
supabase db push

# Or apply the bootstrap script directly
supabase db reset --linked
```

### Option 2: Using psql Command Line

```bash
# Run the bootstrap script via psql
psql "postgresql://postgres:[YOUR_PASSWORD]@db.[YOUR_PROJECT_REF].supabase.co:5432/postgres" \
  -f supabase/sql/bootstrap.sql
```

Replace `[YOUR_PASSWORD]` with your database password and `[YOUR_PROJECT_REF]` with your project reference.

### Option 3: Using Supabase SQL Editor (Manual)

1. Open your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy the entire contents of `supabase/sql/bootstrap.sql`
4. Paste into a new SQL query
5. Click **Run** to execute

## What the Bootstrap Script Does

### 1. Creates Core Tables

- **`public.permits`**: Stores permit data with canonical ID resolution
- **`public.leads`**: Auto-generated leads with enriched metadata

### 2. Adds Duplicate Prevention

- Unique index on `(source, source_record_id)` for permits
- Unique index on `permit_id` for leads
- Unique index on `external_permit_id` for canonical tracking

### 3. Sets Up Automatic Lead Generation

- Trigger function `create_lead_from_permit()` with intelligent field extraction
- Canonical permit ID resolution (permit_id → permit_number → source_record_id → UUID)
- Service categorization (HVAC, Electrical, Plumbing, Roofing, Solar, etc.)
- Metadata enrichment with permit details

### 4. Configures Security Policies

- **Anonymous users**: Read-only access to permits and leads
- **Authenticated users**: Full access to their own data only
- **Service role**: Full access to all data (for backend operations)

### 5. Backfills Existing Data

- Creates leads for any existing permits that don't have associated leads
- Preserves data integrity and relationships

## Verification

After running the bootstrap script, verify the setup:

```sql
-- Check tables were created
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('permits', 'leads');

-- Check trigger function exists
SELECT routine_name FROM information_schema.routines 
WHERE routine_name = 'create_lead_from_permit';

-- Check RLS is enabled
SELECT tablename, rowsecurity FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('permits', 'leads');

-- Test the pipeline with a sample permit
SELECT public.upsert_permit('{"source": "test", "source_record_id": "test-001", "permit_number": "2024-001", "work_description": "HVAC installation", "applicant_name": "Test Applicant", "valuation": "15000"}'::jsonb);

-- Verify lead was created
SELECT name, service, external_permit_id, metadata->>'auto_generated' 
FROM public.leads 
WHERE external_permit_id = '2024-001';
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you're running as a user with sufficient privileges (postgres/owner role)

2. **Extension Not Found**: If PostGIS extension fails to install, your hosting provider may not support it. The script will continue without geospatial features.

3. **Trigger Not Firing**: Check that RLS policies aren't blocking the trigger. Service role should have full access.

4. **Duplicate Key Errors**: If you have existing data that violates unique constraints, clean up duplicates before running the bootstrap.

### Getting Help

- Check the [Supabase Documentation](https://supabase.com/docs)
- Review existing migration files in `supabase/migrations/` for examples
- Examine the trigger function logs in your Supabase dashboard

## API Usage Examples

### Inserting Permits

```javascript
// Using the Supabase client
const { data, error } = await supabase.rpc('upsert_permit', {
  p: {
    source: 'austin',
    source_record_id: 'ATX-2024-12345',
    permit_number: '2024-12345',
    work_description: 'HVAC system replacement',
    applicant_name: 'John Smith',
    address: '123 Main St',
    city: 'Austin',
    county: 'Travis',
    valuation: '12000',
    status: 'issued'
  }
});
```

### Querying Leads

```javascript
// Get recent leads with permit details
const { data, error } = await supabase
  .from('leads')
  .select(`
    *,
    permits:permit_id (
      permit_number,
      work_description,
      issued_date
    )
  `)
  .order('created_at', { ascending: false })
  .limit(10);
```

## Migration Safety

The bootstrap script is designed to be **idempotent** and safe to run multiple times:

- Uses `CREATE TABLE IF NOT EXISTS` for tables
- Uses `CREATE INDEX IF NOT EXISTS` for indexes
- Uses `CREATE OR REPLACE FUNCTION` for functions
- Uses `DROP POLICY IF EXISTS` before creating policies
- Includes conflict resolution in INSERT statements

This means you can safely re-run the script if needed without data loss.