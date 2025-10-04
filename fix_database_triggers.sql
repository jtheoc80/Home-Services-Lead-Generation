-- Fix Database Triggers for Lead Ingestion
-- Run this in Supabase SQL Editor to enable lead creation

-- ===================================================================
-- Step 1: Identify and disable problematic triggers
-- ===================================================================

-- Disable the trigger that's causing issues on the permits table
DO $$ 
BEGIN
    -- Check if trigger exists and disable it
    IF EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trg_lead_from_permit'
    ) THEN
        ALTER TABLE public.permits DISABLE TRIGGER trg_lead_from_permit;
        RAISE NOTICE 'Disabled trg_lead_from_permit trigger';
    END IF;
END $$;

-- ===================================================================
-- Step 2: Create a simple RPC function for lead insertion
-- ===================================================================

CREATE OR REPLACE FUNCTION public.insert_lead_simple(
    p_external_permit_id TEXT,
    p_name TEXT,
    p_address TEXT DEFAULT NULL,
    p_zipcode TEXT DEFAULT NULL,
    p_county TEXT DEFAULT NULL,
    p_trade TEXT DEFAULT NULL,
    p_value NUMERIC DEFAULT NULL,
    p_lead_score NUMERIC DEFAULT NULL,
    p_score_label TEXT DEFAULT NULL,
    p_source TEXT DEFAULT 'api'
)
RETURNS TABLE (
    id UUID,
    external_permit_id TEXT,
    name TEXT,
    created_at TIMESTAMPTZ
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    INSERT INTO public.leads (
        external_permit_id,
        name,
        address,
        zipcode,
        county,
        trade,
        value,
        lead_score,
        score_label,
        source,
        status
    ) VALUES (
        p_external_permit_id,
        p_name,
        p_address,
        p_zipcode,
        p_county,
        p_trade,
        p_value,
        p_lead_score,
        p_score_label,
        p_source,
        'new'
    )
    ON CONFLICT (external_permit_id) 
    DO UPDATE SET
        name = EXCLUDED.name,
        value = EXCLUDED.value,
        lead_score = EXCLUDED.lead_score,
        updated_at = NOW()
    RETURNING 
        leads.id,
        leads.external_permit_id,
        leads.name,
        leads.created_at;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.insert_lead_simple TO anon, authenticated, service_role;

-- ===================================================================
-- Step 3: Test the function
-- ===================================================================

-- Test insert
SELECT * FROM public.insert_lead_simple(
    'TEST-001',
    'Test Company',
    '123 Test St',
    '77002',
    'Harris',
    'Electrical',
    15000,
    85,
    'Hot',
    'test'
);

-- Verify
SELECT id, name, trade, county, lead_score, source 
FROM public.leads 
WHERE external_permit_id = 'TEST-001';

-- Success message
SELECT 'Database triggers fixed! You can now insert leads using the insert_lead_simple function.' AS status;
