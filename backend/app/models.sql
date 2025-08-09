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

  -- Quality tracking fields
  global_score NUMERIC DEFAULT 50,  -- 0-150 range, starts at 50
  last_quality_update TIMESTAMPTZ,

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

CREATE TABLE IF NOT EXISTS notifications (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  lead_id BIGINT NOT NULL,
  channel TEXT NOT NULL CHECK (channel IN ('inapp', 'email', 'sms')),
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'failed', 'read')),
  created_at TIMESTAMPTZ DEFAULT now(),
  sent_at TIMESTAMPTZ
);

-- Lead quality events table for tracking lead scoring events
CREATE TABLE IF NOT EXISTS lead_quality_events (
  id BIGSERIAL PRIMARY KEY,
  lead_id BIGINT NOT NULL REFERENCES leads(id),
  account_id UUID,  -- NULL for global events like decay
  event_type TEXT NOT NULL CHECK (event_type IN ('cancellation', 'feedback_negative', 'decay')),
  weight NUMERIC NOT NULL,  -- Positive or negative weight to apply
  reason_code TEXT,  -- e.g., 'low_quality', 'out_of_area', 'not_qualified'
  metadata JSONB,  -- Additional context
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Cancellations table for tracking subscription cancellations
CREATE TABLE IF NOT EXISTS cancellations (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  reason TEXT NOT NULL,  -- 'low_quality', 'out_of_area', 'too_expensive', etc.
  weight NUMERIC NOT NULL,  -- Weight assigned based on reason
  affected_leads BIGINT[],  -- Array of lead IDs unlocked in last 30 days
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_lead_id ON lead_quality_events(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_created_at ON lead_quality_events(created_at);
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_account_id ON lead_quality_events(account_id);
CREATE INDEX IF NOT EXISTS idx_cancellations_account_id ON cancellations(account_id);
CREATE INDEX IF NOT EXISTS idx_leads_global_score ON leads(global_score);
CREATE INDEX IF NOT EXISTS idx_leads_last_quality_update ON leads(last_quality_update);