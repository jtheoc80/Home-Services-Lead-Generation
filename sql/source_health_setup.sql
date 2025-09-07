-- Source Health Monitoring Schema
-- This file sets up the source_health table and source_health_latest view
-- for the Source Health GitHub Action workflow

-- Create source_health table for storing health check results
CREATE TABLE IF NOT EXISTS source_health (
    id SERIAL PRIMARY KEY,
    source_key TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('online', 'offline', 'limited')),
    last_check TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_time_ms INTEGER,
    error_message TEXT,
    records_available INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_source_health_key_check 
ON source_health (source_key, last_check DESC);

-- Create view to get latest health status for each source
CREATE OR REPLACE VIEW source_health_latest AS
SELECT DISTINCT ON (source_key)
    source_key,
    status,
    last_check,
    response_time_ms,
    error_message,
    records_available,
    metadata
FROM source_health
ORDER BY source_key, last_check DESC;

-- Grant necessary permissions
GRANT SELECT ON source_health TO anon, authenticated;
GRANT SELECT ON source_health_latest TO anon, authenticated;
GRANT INSERT ON source_health TO authenticated;

-- Comment the table and view
COMMENT ON TABLE source_health IS 'Health monitoring data for Texas permit data sources';
COMMENT ON VIEW source_health_latest IS 'Latest health status for each data source';