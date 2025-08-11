-- Add cancellations table for tracking contractor cancellation feedback
-- This enables global and personalized lead scoring based on cancellation patterns

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
  account_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
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

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_cancellations_account_id ON cancellations(account_id);
CREATE INDEX IF NOT EXISTS idx_cancellations_primary_reason ON cancellations(primary_reason);
CREATE INDEX IF NOT EXISTS idx_cancellations_canceled_at ON cancellations(canceled_at);
CREATE INDEX IF NOT EXISTS idx_cancellations_avg_lead_score ON cancellations(avg_lead_score);

-- Add comments for documentation
COMMENT ON TABLE cancellations IS 'Contractor cancellation feedback for lead scoring improvements';
COMMENT ON COLUMN cancellations.primary_reason IS 'Main reason for cancellation';
COMMENT ON COLUMN cancellations.secondary_reasons IS 'Additional contributing factors';
COMMENT ON COLUMN cancellations.total_leads_purchased IS 'Total leads purchased before cancellation';
COMMENT ON COLUMN cancellations.avg_lead_score IS 'Average score of leads purchased by this contractor';
COMMENT ON COLUMN cancellations.preferred_service_areas IS 'Geographic areas contractor prefers';
COMMENT ON COLUMN cancellations.preferred_trade_types IS 'Trade types contractor specializes in';

-- Add cancellation feedback fields to lead scoring
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_cancellation_rate NUMERIC DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_avg_cancellation_score NUMERIC DEFAULT 0;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS personalized_cancellation_adjustment NUMERIC DEFAULT 0;

COMMENT ON COLUMN leads.source_cancellation_rate IS 'Cancellation rate for this lead source (0-1)';
COMMENT ON COLUMN leads.source_avg_cancellation_score IS 'Average score of leads from contractors who later canceled';
COMMENT ON COLUMN leads.personalized_cancellation_adjustment IS 'Score adjustment based on contractor cancellation patterns';