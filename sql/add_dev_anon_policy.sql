-- Add development policy to allow anon SELECT on leads
-- This is specifically for development/testing as mentioned in the requirements

-- Policy for anonymous select (for development)
DROP POLICY IF EXISTS "dev_anon_select_leads" ON public.leads;
CREATE POLICY "dev_anon_select_leads"
    ON public.leads FOR SELECT
    TO anon
    USING (true);

-- Verify the policy was created
SELECT 
    policyname,
    roles,
    cmd AS command,
    permissive,
    qual
FROM pg_policies 
WHERE schemaname = 'public' 
  AND tablename = 'leads'
  AND policyname = 'dev_anon_select_leads';

SELECT 'Development anon SELECT policy added to public.leads!' AS message;