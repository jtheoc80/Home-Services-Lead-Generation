-- Analytics Events Table Migration
-- Create table for storing analytics events for reliable server-side tracking

CREATE TABLE IF NOT EXISTS analytics_events (
    id BIGSERIAL PRIMARY KEY,
    account_id UUID NOT NULL,
    event TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_analytics_events_account_id ON analytics_events(account_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event ON analytics_events(event);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at);

-- Composite index for admin analytics queries
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_created_at ON analytics_events(event, created_at);

-- GIN index for JSONB properties queries
CREATE INDEX IF NOT EXISTS idx_analytics_events_properties ON analytics_events USING gin(properties);

-- Add comment for documentation
COMMENT ON TABLE analytics_events IS 'Stores analytics events for subscription cancellation and reactivation tracking';
COMMENT ON COLUMN analytics_events.account_id IS 'UUID of the user/account associated with the event';
COMMENT ON COLUMN analytics_events.event IS 'Event name (e.g., cancel.confirmed, reactivate.clicked)';
COMMENT ON COLUMN analytics_events.properties IS 'JSON object containing event properties and metadata';
COMMENT ON COLUMN analytics_events.created_at IS 'Timestamp when the event was logged';