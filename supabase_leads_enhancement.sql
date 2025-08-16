-- Supabase leads table enhancement migration
-- Adds the missing fields required for the Next.js dashboard sync
-- Run this after the main supabase_migration.sql

-- Add missing columns to the leads table
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS lead_score INTEGER;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS score_label TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS value NUMERIC;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS permit_id TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS county_population INTEGER;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES auth.users(id);
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS city TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS state TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS zip TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS county TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS service TEXT;

-- Create or update function to automatically set updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to auto-update updated_at
DROP TRIGGER IF EXISTS update_leads_updated_at ON public.leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON public.leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_leads_lead_score ON public.leads(lead_score);
CREATE INDEX IF NOT EXISTS idx_leads_value ON public.leads(value);
CREATE INDEX IF NOT EXISTS idx_leads_permit_id ON public.leads(permit_id);
CREATE INDEX IF NOT EXISTS idx_leads_user_id ON public.leads(user_id);
CREATE INDEX IF NOT EXISTS idx_leads_county ON public.leads(county);
CREATE INDEX IF NOT EXISTS idx_leads_service ON public.leads(service);
CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON public.leads(updated_at);

-- Add some sample data to test the dashboard (optional)
INSERT INTO public.leads (
    name, email, phone, address, city, state, zip, county, service, status, 
    lead_score, score_label, value, permit_id, county_population, source
) VALUES 
    ('John Smith', 'john@example.com', '+1-713-555-0101', '123 Main St', 'Houston', 'TX', '77001', 'Harris', 'HVAC Installation', 'new', 85, 'High', 15000, 'TX2024-001234', 4731145, 'website'),
    ('Sarah Johnson', 'sarah@example.com', '+1-713-555-0102', '456 Oak Ave', 'Houston', 'TX', '77002', 'Harris', 'Electrical Repair', 'qualified', 75, 'Medium', 8500, 'TX2024-001235', 4731145, 'referral'),
    ('Mike Williams', 'mike@example.com', '+1-281-555-0103', '789 Pine St', 'Sugar Land', 'TX', '77478', 'Fort Bend', 'Plumbing', 'contacted', 92, 'High', 12000, 'TX2024-001236', 822779, 'google_ads'),
    ('Lisa Davis', 'lisa@example.com', '+1-281-555-0104', '321 Elm Dr', 'Katy', 'TX', '77494', 'Fort Bend', 'Roofing', 'won', 88, 'High', 25000, 'TX2024-001237', 822779, 'facebook'),
    ('Robert Brown', 'robert@example.com', '+1-713-555-0105', '654 Maple Ln', 'Houston', 'TX', '77003', 'Harris', 'Solar Installation', 'new', 70, 'Medium', 35000, 'TX2024-001238', 4731145, 'website')
ON CONFLICT DO NOTHING;

-- Add comments for documentation
COMMENT ON COLUMN public.leads.lead_score IS 'Lead quality score (0-100)';
COMMENT ON COLUMN public.leads.score_label IS 'Human-readable score label (Low, Medium, High)';
COMMENT ON COLUMN public.leads.value IS 'Estimated project value in dollars';
COMMENT ON COLUMN public.leads.permit_id IS 'Building permit identifier';
COMMENT ON COLUMN public.leads.county_population IS 'Population of the county for demographic analysis';
COMMENT ON COLUMN public.leads.user_id IS 'Associated user/contractor ID for RLS';
COMMENT ON COLUMN public.leads.updated_at IS 'Timestamp of last update (auto-managed)';