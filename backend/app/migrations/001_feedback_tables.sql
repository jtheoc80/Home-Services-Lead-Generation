-- Lead feedback and ML scoring tables migration
-- Creates tables for contractor feedback on leads and ML model scoring outputs

CREATE TYPE lead_rating AS ENUM ('no_answer','bad_contact','not_qualified','quoted','won');

CREATE TABLE IF NOT EXISTS lead_feedback (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  lead_id BIGINT NOT NULL,
  rating lead_rating NOT NULL,
  deal_band TEXT,
  reason_codes TEXT[],
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (account_id, lead_id)
);

CREATE TABLE IF NOT EXISTS lead_outcomes (
  lead_id BIGINT PRIMARY KEY,
  win_label BOOLEAN,
  win_prob NUMERIC,
  calibrated_score NUMERIC,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_lead_feedback_account_id ON lead_feedback(account_id);
CREATE INDEX IF NOT EXISTS idx_lead_feedback_rating ON lead_feedback(rating);
CREATE INDEX IF NOT EXISTS idx_lead_feedback_created_at ON lead_feedback(created_at);
CREATE INDEX IF NOT EXISTS idx_lead_outcomes_win_label ON lead_outcomes(win_label);
CREATE INDEX IF NOT EXISTS idx_lead_outcomes_updated_at ON lead_outcomes(updated_at);

-- Add comments for documentation
COMMENT ON TABLE lead_feedback IS 'Contractor feedback on purchased leads for ML training';
COMMENT ON TABLE lead_outcomes IS 'ML model predictions and scoring for leads';
COMMENT ON COLUMN lead_feedback.rating IS 'Outcome rating from contractor perspective';
COMMENT ON COLUMN lead_feedback.deal_band IS 'Estimated deal value range if won';
COMMENT ON COLUMN lead_feedback.reason_codes IS 'Categorized reasons for the rating';
COMMENT ON COLUMN lead_outcomes.win_label IS 'Binary label for ML training (true=quoted/won)';
COMMENT ON COLUMN lead_outcomes.win_prob IS 'Raw model probability prediction';
COMMENT ON COLUMN lead_outcomes.calibrated_score IS 'Calibrated probability score 0-100';