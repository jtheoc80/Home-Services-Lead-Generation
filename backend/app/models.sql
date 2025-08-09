-- LeadLedgerPro Database Schema
-- Lead feedback collection and ML scoring tables

CREATE TYPE lead_rating AS ENUM ('no_answer','bad_contact','not_qualified','quoted','won');

-- Main leads table to store imported permit/lead data
CREATE TABLE IF NOT EXISTS leads (
  id BIGSERIAL PRIMARY KEY,
  jurisdiction TEXT,
  permit_id TEXT,
  address TEXT,
  description TEXT,
  work_class TEXT,
  category TEXT,
  status TEXT,
  issue_date DATE,
  applicant TEXT,
  owner TEXT,
  value NUMERIC,
  is_residential BOOLEAN,
  scraped_at TIMESTAMPTZ,
  
  -- Enriched location fields
  latitude NUMERIC,
  longitude NUMERIC,
  
  -- Enriched parcel fields
  apn TEXT,
  year_built INTEGER,
  heated_sqft NUMERIC,
  lot_size NUMERIC,
  land_use TEXT,
  
  -- Enriched classification fields
  owner_kind TEXT,
  trade_tags TEXT[],
  budget_band TEXT,
  start_by_estimate DATE,
  
  -- Scoring fields
  lead_score NUMERIC,
  score_recency NUMERIC,
  score_trade_match NUMERIC,
  score_value NUMERIC,
  score_parcel_age NUMERIC,
  score_inspection NUMERIC,
  scoring_version TEXT,
  
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  
  -- Unique constraint on jurisdiction + permit_id to prevent duplicates
  UNIQUE (jurisdiction, permit_id)
);

CREATE TABLE IF NOT EXISTS lead_feedback (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  lead_id BIGINT NOT NULL,
  rating lead_rating NOT NULL,
  deal_band TEXT,             -- '<5k','5-15k','15-50k','50k+'
  reason_codes TEXT[],        -- ['wrong_number','duplicate','low_budget','out_of_area','already_hired']
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (account_id, lead_id)
);

CREATE TABLE IF NOT EXISTS lead_outcomes (
  lead_id BIGINT PRIMARY KEY,
  win_label BOOLEAN,          -- derived: rating in ('quoted','won') -> TRUE; else FALSE
  win_prob NUMERIC,           -- model predicted probability 0..1
  calibrated_score NUMERIC,   -- 0..100
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance optimization

-- Index on jurisdiction for region filtering
CREATE INDEX IF NOT EXISTS idx_leads_jurisdiction ON leads (jurisdiction);

-- Index on lead score for high-value leads
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads (lead_score DESC) WHERE lead_score IS NOT NULL;

-- Index on issue date for recent leads
CREATE INDEX IF NOT EXISTS idx_leads_issue_date ON leads (issue_date DESC) WHERE issue_date IS NOT NULL;

-- Index on residential status for filtering
CREATE INDEX IF NOT EXISTS idx_leads_residential ON leads (is_residential) WHERE is_residential = true;

-- Composite index for common queries (jurisdiction + residential + score)
CREATE INDEX IF NOT EXISTS idx_leads_jurisdiction_residential_score 
ON leads (jurisdiction, is_residential, lead_score DESC) 
WHERE is_residential = true AND lead_score IS NOT NULL;

-- GIN index for trade tags array searches
CREATE INDEX IF NOT EXISTS idx_leads_trade_tags ON leads USING GIN (trade_tags);

-- Geo-spatial indexes for location-based queries
-- Note: These work with standard PostgreSQL. For PostGIS, you'd use different syntax
CREATE INDEX IF NOT EXISTS idx_leads_location ON leads (latitude, longitude) 
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- If PostGIS is available, uncomment the following for better geo performance:
-- CREATE INDEX IF NOT EXISTS idx_leads_point_geom ON leads USING GIST (ST_Point(longitude, latitude))
-- WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Index for feedback table
CREATE INDEX IF NOT EXISTS idx_lead_feedback_account_lead ON lead_feedback (account_id, lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_feedback_rating ON lead_feedback (rating);

-- Index for lead outcomes
CREATE INDEX IF NOT EXISTS idx_lead_outcomes_score ON lead_outcomes (calibrated_score DESC) WHERE calibrated_score IS NOT NULL;