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
  
  -- Cancellation feedback fields
  source_cancellation_rate NUMERIC DEFAULT 0,
  source_avg_cancellation_score NUMERIC DEFAULT 0,
  personalized_cancellation_adjustment NUMERIC DEFAULT 0,
  
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

CREATE TABLE IF NOT EXISTS notification_prefs (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  min_score_threshold NUMERIC DEFAULT 70.0,
  counties TEXT[] DEFAULT ARRAY['tx-harris', 'tx-fort-bend', 'tx-brazoria', 'tx-galveston'],
  -- The '<@' operator is PostgreSQL-specific and means "is contained by": channels must be a subset of ['inapp', 'email', 'sms']
  channels TEXT[] DEFAULT ARRAY['inapp'] CHECK (channels <@ ARRAY['inapp', 'email', 'sms']),
  trade_tags TEXT[],
  value_threshold NUMERIC,
  is_enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (account_id)
);

CREATE TABLE IF NOT EXISTS notifications (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  lead_id BIGINT NOT NULL,
  channel TEXT NOT NULL CHECK (channel IN ('inapp', 'email', 'sms')),
  status TEXT NOT NULL DEFAULT 'queued' CHECK (status IN ('queued', 'sent', 'failed', 'read')),
  title TEXT,
  message TEXT,
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT now(),
  sent_at TIMESTAMPTZ,
  read_at TIMESTAMPTZ
);

-- Subscription and cancellation tables (added for cancellation workflow)
CREATE TYPE subscription_status AS ENUM ('trial', 'active', 'cancelled', 'grace_period', 'expired');
CREATE TYPE subscription_plan AS ENUM ('trial', 'basic', 'premium', 'enterprise');

CREATE TABLE IF NOT EXISTS user_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  plan subscription_plan NOT NULL DEFAULT 'trial',
  status subscription_status NOT NULL DEFAULT 'trial',
  trial_start_date TIMESTAMPTZ,
  trial_end_date TIMESTAMPTZ,
  subscription_start_date TIMESTAMPTZ,
  subscription_end_date TIMESTAMPTZ,
  grace_period_end_date TIMESTAMPTZ,
  billing_cycle TEXT,
  amount_cents INTEGER,
  payment_method TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),

  created_at TIMESTAMPTZ DEFAULT now()
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
  

  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (user_id)
);

CREATE TABLE IF NOT EXISTS cancellation_records (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL,
  subscription_id BIGINT NOT NULL REFERENCES user_subscriptions(id) ON DELETE CASCADE,
  cancellation_type TEXT NOT NULL CHECK (cancellation_type IN ('trial', 'paid')),
  reason_category TEXT,
  reason_notes TEXT,
  cancelled_at TIMESTAMPTZ DEFAULT now(),
  effective_date TIMESTAMPTZ,
  grace_period_days INTEGER DEFAULT 0,
  processed_by UUID,
  refund_issued BOOLEAN DEFAULT false,
  refund_amount_cents INTEGER,

  created_at TIMESTAMPTZ DEFAULT now()

);

-- ===== STRIPE BILLING TABLES =====
-- Billing customers table to map users to Stripe customers
CREATE TABLE IF NOT EXISTS billing_customers (
  user_id UUID PRIMARY KEY,
  email TEXT NOT NULL,
  stripe_customer_id TEXT UNIQUE NOT NULL,
  default_payment_method TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Billing subscriptions table to track Stripe subscriptions
CREATE TABLE IF NOT EXISTS billing_subscriptions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES billing_customers(user_id) ON DELETE CASCADE,
  stripe_subscription_id TEXT UNIQUE NOT NULL,
  status TEXT NOT NULL,
  price_id TEXT NOT NULL,
  quantity INTEGER DEFAULT 1,
  current_period_end TIMESTAMPTZ NOT NULL,
  cancel_at_period_end BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Billing invoices table to track Stripe invoices
CREATE TABLE IF NOT EXISTS billing_invoices (
  stripe_invoice_id TEXT PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES billing_customers(user_id) ON DELETE CASCADE,
  amount_due INTEGER NOT NULL,
  amount_paid INTEGER NOT NULL,
  status TEXT NOT NULL,
  hosted_invoice_url TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Lead credits table to track user credit balances
CREATE TABLE IF NOT EXISTS lead_credits (
  user_id UUID PRIMARY KEY REFERENCES billing_customers(user_id) ON DELETE CASCADE,
  balance INTEGER DEFAULT 0,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Billing events table to log all webhook events
CREATE TABLE IF NOT EXISTS billing_events (
  id BIGSERIAL PRIMARY KEY,
  type TEXT NOT NULL,
  event_id TEXT UNIQUE NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Lead claims table to track claimed leads and credit usage
CREATE TABLE IF NOT EXISTS lead_claims (
  id BIGSERIAL PRIMARY KEY,
  lead_id BIGINT NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  user_id UUID NOT NULL,
  claimed_at TIMESTAMPTZ DEFAULT now(),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(lead_id) -- Prevent duplicate claims on same lead
);

-- Indexes for billing tables
CREATE INDEX IF NOT EXISTS billing_customers_stripe_customer_id_idx ON billing_customers(stripe_customer_id);
CREATE INDEX IF NOT EXISTS billing_subscriptions_user_id_idx ON billing_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS billing_subscriptions_stripe_subscription_id_idx ON billing_subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS billing_subscriptions_status_idx ON billing_subscriptions(status);
CREATE INDEX IF NOT EXISTS billing_invoices_user_id_idx ON billing_invoices(user_id);
CREATE INDEX IF NOT EXISTS billing_invoices_status_idx ON billing_invoices(status);
CREATE INDEX IF NOT EXISTS billing_events_type_idx ON billing_events(type);
CREATE INDEX IF NOT EXISTS billing_events_event_id_idx ON billing_events(event_id);
CREATE INDEX IF NOT EXISTS billing_events_created_at_idx ON billing_events(created_at);
CREATE INDEX IF NOT EXISTS lead_claims_user_id_idx ON lead_claims(user_id);
CREATE INDEX IF NOT EXISTS lead_claims_lead_id_idx ON lead_claims(lead_id);
CREATE INDEX IF NOT EXISTS lead_claims_claimed_at_idx ON lead_claims(claimed_at);