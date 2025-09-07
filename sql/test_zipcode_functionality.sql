-- Comprehensive test script for zipcode backfill and functionality
-- This script tests all zipcode-related functionality including backfill, trigger, and RPC function

-- Test 1: Run the backfill script
\echo 'Running zipcode backfill...'
\i sql/backfill_leads_zipcode.sql

-- Test 2: Test the create_lead_from_permit trigger with zipcode
\echo 'Testing create_lead_from_permit trigger with zipcode...'
INSERT INTO public.permits (
  id, source, source_record_id, permit_id, permit_number, 
  address, city, county, zipcode, permit_type, work_description,
  valuation, status, issued_date, created_at
) VALUES (
  gen_random_uuid(), 'test', 'zipcode-test-1', 'ZC001', 'ZC001',
  '123 Test Street', 'Austin', 'Travis', '78701', 'Residential',
  'HVAC Installation and Repair', 15000, 'Issued', NOW(), NOW()
) ON CONFLICT (source, source_record_id) DO NOTHING;

-- Verify the trigger created a lead with zipcode
SELECT 
  l.id, l.name, l.zip, l.service, p.zipcode as permit_zipcode
FROM public.leads l
INNER JOIN public.permits p ON l.permit_id = p.id
WHERE p.source_record_id = 'zipcode-test-1';

-- Test 3: Test the upsert_leads_from_permits RPC function
\echo 'Testing upsert_leads_from_permits RPC function...'
INSERT INTO public.permits (
  id, source, source_record_id, permit_id, permit_number,
  address, city, county, zipcode, permit_type, work_description,
  valuation, status, issued_date, created_at
) VALUES (
  gen_random_uuid(), 'test', 'zipcode-test-2', 'ZC002', 'ZC002',
  '456 Test Avenue', 'Dallas', 'Dallas', '75201', 'Commercial',
  'Electrical Work', 25000, 'Issued', NOW(), NOW()
) ON CONFLICT (source, source_record_id) DO NOTHING;

-- Run the RPC function for recent permits (last 1 day)
SELECT * FROM public.upsert_leads_from_permits(1);

-- Verify the RPC function created/updated leads with zipcode
SELECT 
  l.id, l.name, l.zip, l.service, l.source, p.zipcode as permit_zipcode
FROM public.leads l
INNER JOIN public.permits p ON l.permit_id = p.id
WHERE p.source_record_id = 'zipcode-test-2';

-- Test 4: Run verification queries
\echo 'Running verification queries...'
\i sql/verify_leads_zipcode.sql

-- Test 5: Summary of zipcode mapping effectiveness
\echo 'Zipcode mapping effectiveness summary:'
SELECT 
  'Total Leads' as metric,
  COUNT(*) as count
FROM public.leads
UNION ALL
SELECT 
  'Leads with ZIP' as metric,
  COUNT(*) as count
FROM public.leads 
WHERE zip IS NOT NULL AND zip != ''
UNION ALL
SELECT 
  'Leads with Permit' as metric,
  COUNT(*) as count
FROM public.leads 
WHERE permit_id IS NOT NULL
UNION ALL
SELECT 
  'Permit-Leads ZIP Match' as metric,
  COUNT(*) as count
FROM public.leads l
INNER JOIN public.permits p ON l.permit_id = p.id
WHERE l.zip = p.zipcode AND l.zip IS NOT NULL AND p.zipcode IS NOT NULL
UNION ALL
SELECT 
  'Permit-Leads ZIP Mismatch' as metric,
  COUNT(*) as count
FROM public.leads l
INNER JOIN public.permits p ON l.permit_id = p.id
WHERE l.zip != p.zipcode AND l.zip IS NOT NULL AND p.zipcode IS NOT NULL;

\echo 'Zipcode backfill and functionality test completed!';