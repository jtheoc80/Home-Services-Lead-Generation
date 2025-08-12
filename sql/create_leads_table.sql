-- Create public.leads table with exact requirements
-- If public.leads isn't present, create it with specified schema and enable RLS
-- Adds temporary anon insert/select policies for testing

-- Enable pgcrypto extension for gen_random_uuid() function
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create public.leads table with exact required schema
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    name TEXT,
    email TEXT,
    phone TEXT,
    source TEXT,
    status TEXT DEFAULT 'new',
    metadata JSONB
);

-- Enable Row Level Security (RLS) on the table
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;

-- Add temporary policies allowing anon role to insert and select all rows for testing
-- Policy for anonymous insert (temporary for testing)
DROP POLICY IF EXISTS "temp_anon_insert_leads" ON public.leads;
CREATE POLICY "temp_anon_insert_leads"
    ON public.leads FOR INSERT
    TO anon
    WITH CHECK (true);

-- Policy for anonymous select (temporary for testing)
DROP POLICY IF EXISTS "temp_anon_select_leads" ON public.leads;
CREATE POLICY "temp_anon_select_leads"
    ON public.leads FOR SELECT
    TO anon
    USING (true);

-- Insert a test record to verify the setup
INSERT INTO public.leads (name, email, phone, source, status, metadata)
VALUES ('Test Lead', 'test@example.com', '+1-555-0100', 'manual', 'new', '{"test": true}')
ON CONFLICT DO NOTHING;

-- Verify the setup
SELECT 'public.leads table created successfully with RLS enabled and temporary anon policies!' AS message;