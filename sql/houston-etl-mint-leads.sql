-- Houston ETL and Lead Generation SQL Script
-- Execute these commands in Supabase SQL Editor to check permits and mint leads
-- as specified in the problem statement

-- Step 1: Check permits count for last 7 days
SELECT 
  count(*) as permits_last_7_days,
  'permits from last 7 days' as description
FROM public.permits 
WHERE issued_date >= now() - interval '7 days';

-- Step 2: Check permits date range and total count
SELECT 
  count(*) as total_permits,
  min(issued_date) as earliest_permit,
  max(issued_date) as latest_permit,
  'total permits in database' as description
FROM public.permits;

-- Step 3: Mint leads from permits (limit 50, last 365 days)
SELECT public.upsert_leads_from_permits_limit(50, 365);

-- Step 4: Check the latest leads generated
SELECT 
  source, 
  external_permit_id, 
  name, 
  county, 
  trade, 
  address, 
  zipcode, 
  created_at 
FROM public.leads 
ORDER BY created_at DESC 
LIMIT 50;

-- Step 5: Count total leads
SELECT 
  count(*) as total_leads,
  count(*) FILTER (WHERE created_at >= now() - interval '1 day') as leads_last_day,
  count(*) FILTER (WHERE created_at >= now() - interval '7 days') as leads_last_7_days,
  'leads summary' as description
FROM public.leads;

-- Step 6: If leads = 0, check recent ETL runs for troubleshooting
SELECT 
  source_system,
  run_timestamp,
  status,
  fetched,
  parsed,
  upserted,
  errors,
  first_issue_date,
  last_issue_date,
  error_message,
  duration_ms
FROM etl_runs 
WHERE source_system = 'city_of_houston' 
ORDER BY run_timestamp DESC 
LIMIT 5;

-- Step 7: Check for constraint or RLS errors by verifying table permissions
-- Check if leads table exists and is accessible
SELECT 
  table_name,
  is_insertable_into,
  is_updatable,
  'table permissions' as description
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('permits', 'leads', 'etl_runs');

-- Step 8: Check RLS policies on leads table
SELECT 
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd,
  qual,
  with_check
FROM pg_policies 
WHERE schemaname = 'public' 
  AND tablename IN ('permits', 'leads', 'etl_runs')
ORDER BY tablename, policyname;