-- ETL Runs Table for Logging ETL Execution Details
-- This table tracks individual ETL runs with metrics and status

CREATE TABLE IF NOT EXISTS etl_runs (
    id BIGSERIAL PRIMARY KEY,
    source_system TEXT NOT NULL,
    run_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL CHECK (status IN ('success', 'error', 'running')) DEFAULT 'running',
    fetched INTEGER NOT NULL DEFAULT 0,
    parsed INTEGER NOT NULL DEFAULT 0,
    upserted INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    first_issue_date DATE,
    last_issue_date DATE,
    error_message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE etl_runs IS 'Logs individual ETL run executions with metrics and status';
COMMENT ON COLUMN etl_runs.source_system IS 'Source system identifier (e.g., city_of_houston)';
COMMENT ON COLUMN etl_runs.run_timestamp IS 'When the ETL run started';
COMMENT ON COLUMN etl_runs.status IS 'Status of the ETL run: success, error, or running';
COMMENT ON COLUMN etl_runs.fetched IS 'Number of records fetched from source';
COMMENT ON COLUMN etl_runs.parsed IS 'Number of records successfully parsed';
COMMENT ON COLUMN etl_runs.upserted IS 'Number of records successfully upserted to database';
COMMENT ON COLUMN etl_runs.errors IS 'Number of errors encountered during processing';
COMMENT ON COLUMN etl_runs.first_issue_date IS 'Earliest issue date in the processed batch';
COMMENT ON COLUMN etl_runs.last_issue_date IS 'Latest issue date in the processed batch';
COMMENT ON COLUMN etl_runs.error_message IS 'Error message if the run failed';
COMMENT ON COLUMN etl_runs.duration_ms IS 'Duration of the ETL run in milliseconds';

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_etl_runs_source_system ON etl_runs(source_system);
CREATE INDEX IF NOT EXISTS idx_etl_runs_run_timestamp ON etl_runs(run_timestamp);
CREATE INDEX IF NOT EXISTS idx_etl_runs_status ON etl_runs(status);
CREATE INDEX IF NOT EXISTS idx_etl_runs_issue_dates ON etl_runs(first_issue_date, last_issue_date);

-- Create a function to update the updated_at timestamp automatically
CREATE OR REPLACE FUNCTION update_etl_runs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update the updated_at column
DROP TRIGGER IF EXISTS update_etl_runs_updated_at_trigger ON etl_runs;
CREATE TRIGGER update_etl_runs_updated_at_trigger
    BEFORE UPDATE ON etl_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_etl_runs_updated_at();

-- Enable Row Level Security (RLS) for security
ALTER TABLE etl_runs ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY IF NOT EXISTS "Service role has full access to etl_runs" ON etl_runs
    FOR ALL USING (auth.role() = 'service_role');

-- Allow authenticated users to read etl_runs for monitoring
CREATE POLICY IF NOT EXISTS "Authenticated users can read etl_runs" ON etl_runs
    FOR SELECT USING (auth.role() = 'authenticated');