-- LeadLedgerPro Database Schema
-- Multi-region lead generation system with configurable jurisdictions

CREATE TYPE lead_rating AS ENUM ('no_answer','bad_contact','not_qualified','quoted','won');

-- Regions: Metro areas, states, national coverage
CREATE TABLE IF NOT EXISTS regions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,         -- e.g., "tx", "tx-houston", "usa"
  name TEXT NOT NULL,                -- "Texas", "Houston Metro", "United States"
  level TEXT NOT NULL,               -- 'metro','state','national'
  parent_id UUID REFERENCES regions(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Jurisdictions: Cities, counties with specific data sources
CREATE TABLE IF NOT EXISTS jurisdictions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,         -- "tx-harris", "tx-galveston-city"
  name TEXT NOT NULL,                -- "Harris County", "City of Galveston"
  region_id UUID REFERENCES regions(id),
  state TEXT NOT NULL,               -- "TX"
  fips TEXT,                         -- optional
  timezone TEXT,                     -- "America/Chicago"
  data_provider TEXT,                -- 'arcgis','accela','opengov','html'
  source_config JSONB NOT NULL,      -- adapter config
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

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
  
  -- Multi-region support
  jurisdiction_id UUID REFERENCES jurisdictions(id),
  region_id UUID REFERENCES regions(id),
  state TEXT,
  lat DOUBLE PRECISION,
  lon DOUBLE PRECISION,
  
  -- Enriched location fields (legacy support)
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

-- PostGIS support (conditional based on extension availability)
-- This will be created conditionally in migrations
-- ALTER TABLE leads ADD COLUMN IF NOT EXISTS geom geometry(Point, 4326);

-- Indexing for geo & search performance
CREATE INDEX IF NOT EXISTS leads_region_idx ON leads(region_id);
CREATE INDEX IF NOT EXISTS leads_jurisdiction_idx ON leads(jurisdiction_id);
CREATE INDEX IF NOT EXISTS leads_state_idx ON leads(state);
CREATE INDEX IF NOT EXISTS leads_score_idx ON leads(lead_score DESC);
CREATE INDEX IF NOT EXISTS leads_lat_lon_idx ON leads(lat, lon);

-- If PostGIS is available, this index will be created:
-- CREATE INDEX IF NOT EXISTS leads_gix ON leads USING GIST(geom);

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

-- Plans: Region-aware pricing and quotas
CREATE TABLE IF NOT EXISTS plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug TEXT UNIQUE NOT NULL,           -- 'starter', 'pro', 'tx-pro', 'national-pro'
  name TEXT NOT NULL,
  monthly_price_cents INT NOT NULL,
  credits INT NOT NULL,
  scope TEXT NOT NULL,                 -- 'metro','state','national'
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS plan_regions (
  plan_id UUID REFERENCES plans(id) ON DELETE CASCADE,
  region_id UUID REFERENCES regions(id) ON DELETE CASCADE,
  PRIMARY KEY(plan_id, region_id)
);

-- Enhanced notification preferences with region support
CREATE TABLE IF NOT EXISTS notification_prefs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id UUID NOT NULL,
  regions TEXT[],                      -- region slugs
  states TEXT[],                       -- state codes  
  jurisdictions TEXT[],                -- jurisdiction slugs
  trade_tags TEXT[],                   -- preferred trades
  min_value NUMERIC,                   -- minimum project value
  email_enabled BOOLEAN DEFAULT TRUE,
  sms_enabled BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);