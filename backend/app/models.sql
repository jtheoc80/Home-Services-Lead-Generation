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
  
  -- Cancellation feedback fields
  source_cancellation_rate NUMERIC DEFAULT 0,
  source_avg_cancellation_score NUMERIC DEFAULT 0,
  personalized_cancellation_adjustment NUMERIC DEFAULT 0,
  
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

CREATE TYPE cancellation_reason AS ENUM (
  'poor_lead_quality',
  'wrong_lead_type', 
  'leads_too_expensive',
  'leads_too_far',
  'leads_not_qualified',
  'too_many_competitors',
  'seasonal_business',
  'financial_issues',
  'business_closure',
  'other'
);

CREATE TABLE IF NOT EXISTS cancellations (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  canceled_at TIMESTAMPTZ DEFAULT now(),
  primary_reason cancellation_reason NOT NULL,
  secondary_reasons cancellation_reason[],
  feedback_text TEXT,
  
  -- Lead source analysis at time of cancellation
  total_leads_purchased INTEGER DEFAULT 0,
  leads_contacted INTEGER DEFAULT 0,
  leads_quoted INTEGER DEFAULT 0,
  leads_won INTEGER DEFAULT 0,
  avg_lead_score NUMERIC,
  
  -- Geographic and trade preferences
  preferred_service_areas TEXT[],
  preferred_trade_types TEXT[],
  
  created_at TIMESTAMPTZ DEFAULT now()
);