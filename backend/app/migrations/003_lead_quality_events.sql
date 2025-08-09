-- Lead quality events migration
-- Creates table for simple thumbs up/down feedback on leads

CREATE TABLE IF NOT EXISTS lead_quality_events (
  id BIGSERIAL PRIMARY KEY,
  account_id UUID NOT NULL,
  lead_id BIGINT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('feedback_positive', 'feedback_negative')),
  weight INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (account_id, lead_id)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_account_created ON lead_quality_events(account_id, created_at);
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_lead_id ON lead_quality_events(lead_id);
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_event_type ON lead_quality_events(event_type);
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_created_at ON lead_quality_events(created_at);

-- Composite index for scoring queries
CREATE INDEX IF NOT EXISTS idx_lead_quality_events_lead_type ON lead_quality_events(lead_id, event_type);

-- Add comments for documentation
COMMENT ON TABLE lead_quality_events IS 'Simple thumbs up/down quality feedback on leads for scoring';
COMMENT ON COLUMN lead_quality_events.account_id IS 'User account identifier who provided the feedback';
COMMENT ON COLUMN lead_quality_events.lead_id IS 'Lead identifier this feedback relates to';
COMMENT ON COLUMN lead_quality_events.event_type IS 'Type of feedback: feedback_positive or feedback_negative';
COMMENT ON COLUMN lead_quality_events.weight IS 'Scoring weight: +5 for positive, -10 for negative';
COMMENT ON COLUMN lead_quality_events.created_at IS 'Timestamp when feedback was first created';
COMMENT ON COLUMN lead_quality_events.updated_at IS 'Timestamp when feedback was last updated (for 24h change window)';