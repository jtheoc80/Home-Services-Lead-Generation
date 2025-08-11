-- Create etl_state table for tracking last successful scraping runs
-- This prevents data gaps and enables incremental data loading

CREATE TABLE IF NOT EXISTS etl_state (
    source TEXT PRIMARY KEY,
    last_run TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for efficient queries
CREATE INDEX IF NOT EXISTS idx_etl_state_last_run ON etl_state(last_run);

-- Add comments for documentation
COMMENT ON TABLE etl_state IS 'Tracks last successful run timestamps for ETL processes';
COMMENT ON COLUMN etl_state.source IS 'Unique identifier for the data source (e.g., harris_issued_permits)';
COMMENT ON COLUMN etl_state.last_run IS 'Timestamp of the last successful data extraction';
COMMENT ON COLUMN etl_state.created_at IS 'When this source was first tracked';
COMMENT ON COLUMN etl_state.updated_at IS 'When this source was last updated';