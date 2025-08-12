-- ETL State Table for Tracking Last Run Timestamps
-- This table helps prevent data gaps and duplicates in ETL processing

CREATE TABLE IF NOT EXISTS etl_state (
    source TEXT PRIMARY KEY,
    last_run TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_success TIMESTAMPTZ,
    status TEXT DEFAULT 'unknown' CHECK (status IN ('success', 'failure', 'running', 'unknown')),
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE etl_state IS 'Tracks ETL state for each data source to prevent gaps and duplicates';
COMMENT ON COLUMN etl_state.source IS 'Unique identifier for the data source (e.g., harris_issued_permits)';
COMMENT ON COLUMN etl_state.last_run IS 'Timestamp of the last ETL run attempt';
COMMENT ON COLUMN etl_state.last_success IS 'Timestamp of the last successful ETL run';
COMMENT ON COLUMN etl_state.status IS 'Current status of the ETL source';
COMMENT ON COLUMN etl_state.records_processed IS 'Number of records processed in the last run';
COMMENT ON COLUMN etl_state.error_message IS 'Error message from the last failed run';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_etl_state_last_run ON etl_state(last_run);
CREATE INDEX IF NOT EXISTS idx_etl_state_status ON etl_state(status);

-- Create a function to update the updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_etl_state_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update the updated_at column
DROP TRIGGER IF EXISTS update_etl_state_updated_at_trigger ON etl_state;
CREATE TRIGGER update_etl_state_updated_at_trigger
    BEFORE UPDATE ON etl_state
    FOR EACH ROW
    EXECUTE FUNCTION update_etl_state_updated_at();

-- Insert some initial source entries
INSERT INTO etl_state (source, status) VALUES 
    ('harris_issued_permits', 'unknown'),
    ('houston_city_permits', 'unknown'),
    ('fort_bend_permits', 'unknown'),
    ('brazoria_permits', 'unknown'),
    ('galveston_permits', 'unknown')
ON CONFLICT (source) DO NOTHING;

-- Example queries for using this table:

-- Get last run time for a source (with 1-minute overlap to avoid gaps)
-- SELECT last_run - INTERVAL '1 minute' as query_since 
-- FROM etl_state 
-- WHERE source = 'harris_issued_permits';

-- Update state after successful run
-- UPDATE etl_state 
-- SET last_run = NOW(), 
--     last_success = NOW(), 
--     status = 'success', 
--     records_processed = 150,
--     error_message = NULL
-- WHERE source = 'harris_issued_permits';

-- Update state after failed run
-- UPDATE etl_state 
-- SET last_run = NOW(), 
--     status = 'failure', 
--     records_processed = 0,
--     error_message = 'Connection timeout to data source'
-- WHERE source = 'harris_issued_permits';