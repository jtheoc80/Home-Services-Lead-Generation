-- Supabase SQL Migration Script
-- Creates tables: public.leads, public.contractors, public.lead_feedback, public.contractor_engagement
-- Enables RLS on all four tables with appropriate policies
-- Run this script in Supabase SQL Editor

-- Note: leads and lead_feedback tables may already exist in your database
-- This script uses IF NOT EXISTS to avoid conflicts

-- Create contractors table for authenticated users
CREATE TABLE IF NOT EXISTS public.contractors (
  id UUID PRIMARY KEY DEFAULT auth.uid(),
  email TEXT UNIQUE NOT NULL,
  company_name TEXT,
  phone TEXT,
  trade_specialties TEXT[],
  service_areas TEXT[],
  license_number TEXT,
  is_verified BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create contractor_engagement table to track contractor interactions with leads
CREATE TABLE IF NOT EXISTS public.contractor_engagement (
  id BIGSERIAL PRIMARY KEY,
  contractor_id UUID NOT NULL REFERENCES public.contractors(id) ON DELETE CASCADE,
  lead_id BIGINT NOT NULL REFERENCES public.leads(id) ON DELETE CASCADE,
  engagement_type TEXT NOT NULL CHECK (engagement_type IN ('viewed', 'contacted', 'quoted', 'won', 'lost')),
  engagement_date TIMESTAMPTZ DEFAULT now(),
  notes TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (contractor_id, lead_id, engagement_type)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_contractors_email ON public.contractors(email);
CREATE INDEX IF NOT EXISTS idx_contractors_trade_specialties ON public.contractors USING GIN(trade_specialties);
CREATE INDEX IF NOT EXISTS idx_contractors_service_areas ON public.contractors USING GIN(service_areas);
CREATE INDEX IF NOT EXISTS idx_contractors_created_at ON public.contractors(created_at);

CREATE INDEX IF NOT EXISTS idx_contractor_engagement_contractor_id ON public.contractor_engagement(contractor_id);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_lead_id ON public.contractor_engagement(lead_id);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_type ON public.contractor_engagement(engagement_type);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_date ON public.contractor_engagement(engagement_date);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_contractor_lead ON public.contractor_engagement(contractor_id, lead_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contractors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.lead_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.contractor_engagement ENABLE ROW LEVEL SECURITY;

-- Add missing foreign key constraint to lead_feedback table (if needed)
-- This may fail if the constraint already exists or if the table structure is different
DO $$ 
BEGIN
    ALTER TABLE public.lead_feedback ADD CONSTRAINT fk_lead_feedback_lead_id 
      FOREIGN KEY (lead_id) REFERENCES public.leads(id) ON DELETE CASCADE;
EXCEPTION 
    WHEN duplicate_object THEN NULL;
END $$;

/*
 * IMPORTANT: Run this migration AFTER smoke tests pass
 * 
 * This migration replaces temporary anonymous policies with authenticated-only policies.
 * The anonymous policies were temporary and are now being replaced with secure 
 * authenticated access for both INSERT and SELECT operations on the leads table.
 */

-- Policies for leads table
-- Drop temporary anonymous policies (these were for initial testing only)
DROP POLICY IF EXISTS "Allow anonymous insert on leads" ON public.leads;
DROP POLICY IF EXISTS "anon_can_insert_leads" ON public.leads;

-- Create authenticated-only policies that allow all rows for authenticated users
DROP POLICY IF EXISTS "auth_can_insert" ON public.leads;
CREATE POLICY "auth_can_insert"
  ON public.leads FOR INSERT
  TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS "auth_can_select" ON public.leads;
CREATE POLICY "auth_can_select"
  ON public.leads FOR SELECT
  TO authenticated
  USING (true);

-- Remove legacy authenticated policies (replaced by the new standardized ones above)
DROP POLICY IF EXISTS "Allow authenticated select on leads" ON public.leads;

-- Policies for contractors table
-- Allow authenticated users to select and update their own contractor profile
DROP POLICY IF EXISTS "Allow contractors to select own profile" ON public.contractors;
CREATE POLICY "Allow contractors to select own profile"
  ON public.contractors FOR SELECT
  TO authenticated
  USING (id = auth.uid());

DROP POLICY IF EXISTS "Allow contractors to update own profile" ON public.contractors;
CREATE POLICY "Allow contractors to update own profile"
  ON public.contractors FOR UPDATE
  TO authenticated
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

DROP POLICY IF EXISTS "Allow contractors to insert own profile" ON public.contractors;
CREATE POLICY "Allow contractors to insert own profile"
  ON public.contractors FOR INSERT
  TO authenticated
  WITH CHECK (id = auth.uid());

-- Policies for lead_feedback table
-- Allow authenticated users to insert and select their own feedback
DROP POLICY IF EXISTS "Allow contractors to insert own feedback" ON public.lead_feedback;
CREATE POLICY "Allow contractors to insert own feedback"
  ON public.lead_feedback FOR INSERT
  TO authenticated
  WITH CHECK (account_id = auth.uid());

DROP POLICY IF EXISTS "Allow contractors to select own feedback" ON public.lead_feedback;
CREATE POLICY "Allow contractors to select own feedback"
  ON public.lead_feedback FOR SELECT
  TO authenticated
  USING (account_id = auth.uid());

-- Policies for contractor_engagement table
-- Allow authenticated users to insert and select their own engagement records
DROP POLICY IF EXISTS "Allow contractors to insert own engagement" ON public.contractor_engagement;
CREATE POLICY "Allow contractors to insert own engagement"
  ON public.contractor_engagement FOR INSERT
  TO authenticated
  WITH CHECK (contractor_id = auth.uid());

DROP POLICY IF EXISTS "Allow contractors to select own engagement" ON public.contractor_engagement;
CREATE POLICY "Allow contractors to select own engagement"
  ON public.contractor_engagement FOR SELECT
  TO authenticated
  USING (contractor_id = auth.uid());

DROP POLICY IF EXISTS "Allow contractors to update own engagement" ON public.contractor_engagement;
CREATE POLICY "Allow contractors to update own engagement"
  ON public.contractor_engagement FOR UPDATE
  TO authenticated
  USING (contractor_id = auth.uid())
  WITH CHECK (contractor_id = auth.uid());

-- Add comments for documentation
COMMENT ON TABLE public.contractors IS 'Contractor profiles for authenticated users';
COMMENT ON TABLE public.contractor_engagement IS 'Tracks contractor interactions with leads';

COMMENT ON COLUMN public.contractors.id IS 'User ID from Supabase auth, defaults to auth.uid()';
COMMENT ON COLUMN public.contractors.email IS 'Contractor email address';
COMMENT ON COLUMN public.contractors.company_name IS 'Business or company name';
COMMENT ON COLUMN public.contractors.trade_specialties IS 'Array of contractor specialties (roofing, plumbing, etc.)';
COMMENT ON COLUMN public.contractors.service_areas IS 'Array of geographic service areas';
COMMENT ON COLUMN public.contractors.license_number IS 'Professional license number if applicable';
COMMENT ON COLUMN public.contractors.is_verified IS 'Whether contractor has been verified';

COMMENT ON COLUMN public.contractor_engagement.contractor_id IS 'References contractors.id (auth.uid())';
COMMENT ON COLUMN public.contractor_engagement.lead_id IS 'References leads.id';
COMMENT ON COLUMN public.contractor_engagement.engagement_type IS 'Type of interaction: viewed, contacted, quoted, won, lost';
COMMENT ON COLUMN public.contractor_engagement.engagement_date IS 'When the engagement occurred';
COMMENT ON COLUMN public.contractor_engagement.metadata IS 'Additional structured data about the engagement';

-- Success message
SELECT 'Supabase migration completed successfully!' as message;