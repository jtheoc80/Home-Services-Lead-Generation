-- Add unique index on permits (source, source_record_id) to prevent duplicates
-- This ensures upsert operations work correctly by (source, source_record_id) pair

-- Create unique index if it doesn't exist
CREATE UNIQUE INDEX IF NOT EXISTS uq_permits_source_key 
ON permits (source, source_record_id);

-- Comment for documentation
COMMENT ON INDEX uq_permits_source_key IS 'Unique index to prevent duplicate permits from same source with same source_record_id';