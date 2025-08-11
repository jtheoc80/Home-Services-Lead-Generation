-- Test queries for Supabase migration
-- Run these after executing the main migration to verify functionality

-- Test 1: Create a contractor profile (should work for authenticated users)
-- This would be run by an authenticated user where auth.uid() returns their user ID
/*
INSERT INTO public.contractors (email, company_name, trade_specialties, service_areas) 
VALUES (
  'contractor@example.com', 
  'Example Roofing Co',
  ARRAY['roofing', 'gutters'],
  ARRAY['tx-harris', 'tx-fort-bend']
);
*/

-- Test 2: Select own contractor profile (should work)
/*
SELECT * FROM public.contractors WHERE id = auth.uid();
*/

-- Test 3: Try to select another contractor's profile (should return no results due to RLS)
/*
SELECT * FROM public.contractors WHERE id != auth.uid();
*/

-- Test 4: Insert a lead as authenticated user (anonymous access no longer supported)
-- This test should be run as an authenticated user since anonymous policies have been removed
/*
INSERT INTO public.leads (jurisdiction, permit_id, address, description, work_class, category, status, issue_date, applicant, owner, value, is_residential)
VALUES (
  'houston',
  'TEST-2024-001',
  '123 Test St, Houston, TX 77001',
  'Roof replacement',
  'Roofing',
  'Residential',
  'Issued',
  '2024-01-15',
  'John Doe',
  'John Doe',
  25000,
  true
);
*/

-- Test 5: Select leads as authenticated user (should work)
/*
SELECT id, jurisdiction, permit_id, address, description, work_class 
FROM public.leads 
LIMIT 5;
*/

-- Test 6: Insert lead feedback (should work for authenticated users)
/*
INSERT INTO public.lead_feedback (lead_id, rating, deal_band, notes)
VALUES (
  1, -- Replace with actual lead ID
  'quoted',
  '15-50k',
  'Provided quote for roof replacement'
);
*/

-- Test 7: Select own lead feedback (should work)
/*
SELECT * FROM public.lead_feedback WHERE account_id = auth.uid();
*/

-- Test 8: Insert contractor engagement (should work for authenticated users)
/*
INSERT INTO public.contractor_engagement (lead_id, engagement_type, notes)
VALUES (
  1, -- Replace with actual lead ID
  'contacted',
  'Called homeowner, left voicemail'
);
*/

-- Test 9: Select own contractor engagement (should work)
/*
SELECT * FROM public.contractor_engagement WHERE contractor_id = auth.uid();
*/

-- Test 10: Verify RLS is enabled on all tables
SELECT 
  schemaname,
  tablename,
  rowsecurity
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('leads', 'contractors', 'lead_feedback', 'contractor_engagement')
ORDER BY tablename;