-- Test queries to verify the permits_raw_harris table setup
-- Run these after executing permits_raw_harris_setup.sql

-- 1. Verify table structure and columns
SELECT 
    column_name,
    data_type,
    column_default,
    is_nullable,
    ordinal_position
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'permits_raw_harris'
ORDER BY ordinal_position;

-- 2. Verify RLS is disabled (should show rowsecurity = false)
SELECT 
    schemaname, 
    tablename, 
    rowsecurity
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename = 'permits_raw_harris';

-- 3. Verify indexes exist
SELECT 
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
  AND tablename = 'permits_raw_harris'
ORDER BY indexname;

-- 4. Verify primary key constraint
SELECT 
    conname,
    contype,
    conkey,
    confkey
FROM pg_constraint 
WHERE conrelid = 'public.permits_raw_harris'::regclass
  AND contype = 'p';

-- 5. Test insert sample data
INSERT INTO public.permits_raw_harris (
    event_id,
    permit_number,
    permit_name,
    app_type,
    issue_date,
    project_number,
    full_address,
    street_number,
    street_name,
    status,
    raw
) VALUES (
    123456789,
    'BP2024-001234',
    'Single Family Residence',
    'Building',
    '2024-01-15T10:00:00Z'::timestamptz,
    'PRJ-2024-001',
    '123 Main Street, Houston, TX 77001',
    123,
    'Main Street',
    'Issued',
    '{"original_data": "test_permit", "source": "harris_county"}'::jsonb
);

-- 6. Verify data was inserted correctly
SELECT 
    event_id,
    permit_number,
    permit_name,
    app_type,
    issue_date,
    project_number,
    full_address,
    street_number,
    street_name,
    status,
    raw,
    created_at
FROM public.permits_raw_harris 
WHERE event_id = 123456789;

-- 7. Test index performance on issue_date (should use idx_permits_harris_issue_date)
EXPLAIN (ANALYZE, BUFFERS) 
SELECT * 
FROM public.permits_raw_harris 
WHERE issue_date >= '2024-01-01T00:00:00Z'::timestamptz 
ORDER BY issue_date DESC 
LIMIT 10;

-- 8. Test index performance on permit_number 
EXPLAIN (ANALYZE, BUFFERS)
SELECT * 
FROM public.permits_raw_harris 
WHERE permit_number = 'BP2024-001234';

-- 9. Verify table comments exist
SELECT 
    obj_description('public.permits_raw_harris'::regclass) as table_comment;

-- 10. Verify column comments exist
SELECT 
    column_name,
    col_description('public.permits_raw_harris'::regclass, ordinal_position) as column_comment
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'permits_raw_harris'
  AND col_description('public.permits_raw_harris'::regclass, ordinal_position) IS NOT NULL
ORDER BY ordinal_position;

-- Cleanup test data
DELETE FROM public.permits_raw_harris WHERE event_id = 123456789;

-- Final verification
SELECT 'Harris County permits raw table tests completed successfully!' as message;