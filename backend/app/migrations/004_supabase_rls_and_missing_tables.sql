-- Supabase RLS and missing tables migration
-- Creates missing contractors and contractor_engagement tables
-- Enables Row Level Security (RLS) on all tables
-- Creates Supabase auth policies for proper access control

-- Create contractors table for authenticated users
CREATE TABLE IF NOT EXISTS contractors (
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
CREATE TABLE IF NOT EXISTS contractor_engagement (
  id BIGSERIAL PRIMARY KEY,
  contractor_id UUID NOT NULL REFERENCES contractors(id) ON DELETE CASCADE,
  lead_id BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  engagement_type TEXT NOT NULL CHECK (engagement_type IN ('viewed', 'contacted', 'quoted', 'won', 'lost')),
  engagement_date TIMESTAMPTZ DEFAULT now(),
  notes TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (contractor_id, lead_id, engagement_type)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_contractors_email ON contractors(email);
CREATE INDEX IF NOT EXISTS idx_contractors_trade_specialties ON contractors USING GIN(trade_specialties);
CREATE INDEX IF NOT EXISTS idx_contractors_service_areas ON contractors USING GIN(service_areas);
CREATE INDEX IF NOT EXISTS idx_contractors_created_at ON contractors(created_at);

CREATE INDEX IF NOT EXISTS idx_contractor_engagement_contractor_id ON contractor_engagement(contractor_id);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_lead_id ON contractor_engagement(lead_id);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_type ON contractor_engagement(engagement_type);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_date ON contractor_engagement(engagement_date);
CREATE INDEX IF NOT EXISTS idx_contractor_engagement_contractor_lead ON contractor_engagement(contractor_id, lead_id);

-- Enable Row Level Security (RLS) on all tables
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE contractors ENABLE ROW LEVEL SECURITY;
ALTER TABLE lead_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE contractor_engagement ENABLE ROW LEVEL SECURITY;

-- Add missing foreign key constraint to lead_feedback table
ALTER TABLE lead_feedback ADD CONSTRAINT fk_lead_feedback_lead_id 
  FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE;

-- Policies for leads table
-- Allow anonymous users to insert leads (for public lead forms)
CREATE POLICY "Allow anonymous insert on leads"
  ON leads FOR INSERT
  TO anon
  WITH CHECK (true);

-- Allow authenticated users to select all leads
CREATE POLICY "Allow authenticated select on leads"
  ON leads FOR SELECT
  TO authenticated
  USING (true);

-- Policies for contractors table
-- Allow authenticated users to select and update their own contractor profile
CREATE POLICY "Allow contractors to select own profile"
  ON contractors FOR SELECT
  TO authenticated
  USING (id = auth.uid());

CREATE POLICY "Allow contractors to update own profile"
  ON contractors FOR UPDATE
  TO authenticated
  USING (id = auth.uid())
  WITH CHECK (id = auth.uid());

CREATE POLICY "Allow contractors to insert own profile"
  ON contractors FOR INSERT
  TO authenticated
  WITH CHECK (id = auth.uid());

-- Policies for lead_feedback table
-- Allow authenticated users to insert and select their own feedback
CREATE POLICY "Allow contractors to insert own feedback"
  ON lead_feedback FOR INSERT
  TO authenticated
  WITH CHECK (account_id = auth.uid());

CREATE POLICY "Allow contractors to select own feedback"
  ON lead_feedback FOR SELECT
  TO authenticated
  USING (account_id = auth.uid());

-- Policies for contractor_engagement table
-- Allow authenticated users to insert and select their own engagement records
CREATE POLICY "Allow contractors to insert own engagement"
  ON contractor_engagement FOR INSERT
  TO authenticated
  WITH CHECK (contractor_id = auth.uid());

CREATE POLICY "Allow contractors to select own engagement"
  ON contractor_engagement FOR SELECT
  TO authenticated
  USING (contractor_id = auth.uid());

CREATE POLICY "Allow contractors to update own engagement"
  ON contractor_engagement FOR UPDATE
  TO authenticated
  USING (contractor_id = auth.uid())
  WITH CHECK (contractor_id = auth.uid());

-- Add comments for documentation
COMMENT ON TABLE contractors IS 'Contractor profiles for authenticated users';
COMMENT ON TABLE contractor_engagement IS 'Tracks contractor interactions with leads';

COMMENT ON COLUMN contractors.id IS 'User ID from Supabase auth, defaults to auth.uid()';
COMMENT ON COLUMN contractors.email IS 'Contractor email address';
COMMENT ON COLUMN contractors.company_name IS 'Business or company name';
COMMENT ON COLUMN contractors.trade_specialties IS 'Array of contractor specialties (roofing, plumbing, etc.)';
COMMENT ON COLUMN contractors.service_areas IS 'Array of geographic service areas';
COMMENT ON COLUMN contractors.license_number IS 'Professional license number if applicable';
COMMENT ON COLUMN contractors.is_verified IS 'Whether contractor has been verified';

COMMENT ON COLUMN contractor_engagement.contractor_id IS 'References contractors.id (auth.uid())';
COMMENT ON COLUMN contractor_engagement.lead_id IS 'References leads.id';
COMMENT ON COLUMN contractor_engagement.engagement_type IS 'Type of interaction: viewed, contacted, quoted, won, lost';
COMMENT ON COLUMN contractor_engagement.engagement_date IS 'When the engagement occurred';
COMMENT ON COLUMN contractor_engagement.metadata IS 'Additional structured data about the engagement';