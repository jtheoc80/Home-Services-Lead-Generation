-- ===================================================================
-- 2025 Database Setup - Real Schema with PostGIS and Security
-- ===================================================================
-- This migration sets up the production database schema with:
-- - PostGIS extension for spatial data
-- - Multi-schema architecture (raw, bronze, silver, gold, meta)
-- - Real tables for permits, violations, inspections, bids, awards, contractors
-- - Optimized indexes (BRIN, GIST, btree)
-- - Row Level Security (RLS) on all gold tables
-- ===================================================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- Create schemas for data pipeline
CREATE SCHEMA IF NOT EXISTS raw;      -- Raw extracted data
CREATE SCHEMA IF NOT EXISTS bronze;   -- Basic normalization
CREATE SCHEMA IF NOT EXISTS silver;   -- Business logic applied
CREATE SCHEMA IF NOT EXISTS gold;     -- Production-ready data
CREATE SCHEMA IF NOT EXISTS meta;     -- Metadata and state tracking

-- ===================================================================
-- META SCHEMA - Sources registry and ingestion state
-- ===================================================================

-- Sources registry table
CREATE TABLE IF NOT EXISTS meta.sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    kind TEXT NOT NULL CHECK (kind IN ('arcgis', 'socrata', 'csv_http', 'tpia')),
    endpoint TEXT,
    updated_field TEXT,
    primary_key TEXT,
    cadence TEXT NOT NULL CHECK (cadence IN ('daily', 'weekly', 'monthly')),
    entity TEXT NOT NULL CHECK (entity IN ('permits', 'violations', 'inspections', 'bids', 'awards', 'contractors')),
    license TEXT,
    provenance_url TEXT,
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Ingestion state tracking
CREATE TABLE IF NOT EXISTS meta.ingest_state (
    source_id TEXT REFERENCES meta.sources(id),
    last_updated_seen TIMESTAMPTZ,
    last_status TEXT NOT NULL CHECK (last_status IN ('success', 'error', 'manual', 'running')),
    last_run TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    PRIMARY KEY (source_id)
);

-- ===================================================================
-- GOLD SCHEMA - Production tables with full optimization
-- ===================================================================

-- Gold permits table
CREATE TABLE IF NOT EXISTS gold.permits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    permit_id TEXT NOT NULL,
    source_id TEXT REFERENCES meta.sources(id),
    issued_at TIMESTAMPTZ,
    address TEXT,
    city TEXT,
    county TEXT,
    zipcode TEXT,
    description TEXT,
    permit_type TEXT,
    permit_class TEXT,
    status TEXT,
    applicant_name TEXT,
    contractor_name TEXT,
    owner_name TEXT,
    valuation NUMERIC,
    square_feet INTEGER,
    stories INTEGER,
    units INTEGER,
    geom GEOMETRY(POINT, 4326),
    trade_tags TEXT[],
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(permit_id, source_id)
);

-- Gold violations table
CREATE TABLE IF NOT EXISTS gold.violations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT NOT NULL,
    source_id TEXT REFERENCES meta.sources(id),
    violation_date TIMESTAMPTZ,
    address TEXT,
    city TEXT,
    county TEXT,
    zipcode TEXT,
    violation_type TEXT,
    violation_code TEXT,
    description TEXT,
    status TEXT,
    inspector_name TEXT,
    property_owner TEXT,
    geom GEOMETRY(POINT, 4326),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(case_id, source_id)
);

-- Gold inspections table
CREATE TABLE IF NOT EXISTS gold.inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    inspection_id TEXT NOT NULL,
    permit_id TEXT,
    source_id TEXT REFERENCES meta.sources(id),
    scheduled_date TIMESTAMPTZ,
    completed_date TIMESTAMPTZ,
    address TEXT,
    city TEXT,
    county TEXT,
    zipcode TEXT,
    inspection_type TEXT,
    result TEXT,
    inspector_name TEXT,
    notes TEXT,
    geom GEOMETRY(POINT, 4326),
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(inspection_id, source_id)
);

-- Gold bids table
CREATE TABLE IF NOT EXISTS gold.bids (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bid_id TEXT NOT NULL,
    source_id TEXT REFERENCES meta.sources(id),
    posted_date TIMESTAMPTZ,
    closing_date TIMESTAMPTZ,
    title TEXT,
    description TEXT,
    agency TEXT,
    category TEXT,
    estimated_value NUMERIC,
    location TEXT,
    contact_email TEXT,
    contact_phone TEXT,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(bid_id, source_id)
);

-- Gold awards table
CREATE TABLE IF NOT EXISTS gold.awards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_id TEXT NOT NULL,
    bid_id TEXT,
    source_id TEXT REFERENCES meta.sources(id),
    award_date TIMESTAMPTZ,
    vendor_name TEXT,
    vendor_address TEXT,
    title TEXT,
    description TEXT,
    agency TEXT,
    award_amount NUMERIC,
    contract_start TIMESTAMPTZ,
    contract_end TIMESTAMPTZ,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(contract_id, source_id)
);

-- Gold contractors table
CREATE TABLE IF NOT EXISTS gold.contractors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    license_number TEXT NOT NULL,
    source_id TEXT REFERENCES meta.sources(id),
    business_name TEXT,
    owner_name TEXT,
    license_type TEXT,
    specialty TEXT,
    address TEXT,
    city TEXT,
    county TEXT,
    zipcode TEXT,
    phone TEXT,
    email TEXT,
    license_status TEXT,
    issue_date DATE,
    expiration_date DATE,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(license_number, source_id)
);

-- Lead scores table
CREATE TABLE IF NOT EXISTS gold.lead_scores (
    lead_id UUID NOT NULL,
    version TEXT NOT NULL,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    reasons JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (lead_id, version)
);

-- ===================================================================
-- OPTIMIZED INDEXES
-- ===================================================================

-- BRIN indexes on date fields (efficient for time-series data)
CREATE INDEX IF NOT EXISTS idx_permits_issued_at_brin ON gold.permits USING BRIN (issued_at);
CREATE INDEX IF NOT EXISTS idx_violations_date_brin ON gold.violations USING BRIN (violation_date);
CREATE INDEX IF NOT EXISTS idx_inspections_completed_brin ON gold.inspections USING BRIN (completed_date);
CREATE INDEX IF NOT EXISTS idx_bids_posted_brin ON gold.bids USING BRIN (posted_date);
CREATE INDEX IF NOT EXISTS idx_awards_date_brin ON gold.awards USING BRIN (award_date);

-- GIST indexes on geometry fields
CREATE INDEX IF NOT EXISTS idx_permits_geom ON gold.permits USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_violations_geom ON gold.violations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_inspections_geom ON gold.inspections USING GIST (geom);

-- B-tree indexes on (county, city) for geographic filtering
CREATE INDEX IF NOT EXISTS idx_permits_county_city ON gold.permits (county, city);
CREATE INDEX IF NOT EXISTS idx_violations_county_city ON gold.violations (county, city);
CREATE INDEX IF NOT EXISTS idx_inspections_county_city ON gold.inspections (county, city);

-- B-tree indexes on source_id for data lineage
CREATE INDEX IF NOT EXISTS idx_permits_source ON gold.permits (source_id);
CREATE INDEX IF NOT EXISTS idx_violations_source ON gold.violations (source_id);
CREATE INDEX IF NOT EXISTS idx_inspections_source ON gold.inspections (source_id);
CREATE INDEX IF NOT EXISTS idx_bids_source ON gold.bids (source_id);
CREATE INDEX IF NOT EXISTS idx_awards_source ON gold.awards (source_id);
CREATE INDEX IF NOT EXISTS idx_contractors_source ON gold.contractors (source_id);

-- Full-text search indexes
CREATE INDEX IF NOT EXISTS idx_permits_description_gin ON gold.permits USING GIN (to_tsvector('english', description));
CREATE INDEX IF NOT EXISTS idx_violations_description_gin ON gold.violations USING GIN (to_tsvector('english', description));

-- Trade tags array index
CREATE INDEX IF NOT EXISTS idx_permits_trade_tags ON gold.permits USING GIN (trade_tags);

-- Lead scores indexes
CREATE INDEX IF NOT EXISTS idx_lead_scores_score ON gold.lead_scores (score DESC);
CREATE INDEX IF NOT EXISTS idx_lead_scores_created ON gold.lead_scores (created_at DESC);

-- ===================================================================
-- ROW LEVEL SECURITY (RLS)
-- ===================================================================

-- Enable RLS on all gold tables
ALTER TABLE gold.permits ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.violations ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.inspections ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.bids ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.awards ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.contractors ENABLE ROW LEVEL SECURITY;
ALTER TABLE gold.lead_scores ENABLE ROW LEVEL SECURITY;

-- Read-only policy for authenticated users
CREATE POLICY IF NOT EXISTS "Allow read access for authenticated users" ON gold.permits
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "Allow read access for authenticated users" ON gold.violations
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "Allow read access for authenticated users" ON gold.inspections
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "Allow read access for authenticated users" ON gold.bids
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "Allow read access for authenticated users" ON gold.awards
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "Allow read access for authenticated users" ON gold.contractors
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY IF NOT EXISTS "Allow read access for authenticated users" ON gold.lead_scores
    FOR SELECT USING (auth.role() = 'authenticated');

-- Write policy restricted to service role
CREATE POLICY IF NOT EXISTS "Allow write access for service role" ON gold.permits
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Allow write access for service role" ON gold.violations
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Allow write access for service role" ON gold.inspections
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Allow write access for service role" ON gold.bids
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Allow write access for service role" ON gold.awards
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Allow write access for service role" ON gold.contractors
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY IF NOT EXISTS "Allow write access for service role" ON gold.lead_scores
    FOR ALL USING (auth.role() = 'service_role');

-- ===================================================================
-- TRIGGERS FOR UPDATED_AT
-- ===================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all gold tables
DO $$
BEGIN
    -- Check if triggers exist before creating them
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_permits_updated_at') THEN
        CREATE TRIGGER update_permits_updated_at BEFORE UPDATE ON gold.permits
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_violations_updated_at') THEN
        CREATE TRIGGER update_violations_updated_at BEFORE UPDATE ON gold.violations
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_inspections_updated_at') THEN
        CREATE TRIGGER update_inspections_updated_at BEFORE UPDATE ON gold.inspections
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_bids_updated_at') THEN
        CREATE TRIGGER update_bids_updated_at BEFORE UPDATE ON gold.bids
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_awards_updated_at') THEN
        CREATE TRIGGER update_awards_updated_at BEFORE UPDATE ON gold.awards
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'update_contractors_updated_at') THEN
        CREATE TRIGGER update_contractors_updated_at BEFORE UPDATE ON gold.contractors
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- ===================================================================
-- VIEWS FOR COMMON QUERIES
-- ===================================================================

-- Recent permits view (last 30 days)
CREATE OR REPLACE VIEW gold.recent_permits AS
SELECT 
    id,
    permit_id,
    issued_at,
    address,
    city,
    county,
    description,
    permit_type,
    applicant_name,
    contractor_name,
    valuation,
    geom
FROM gold.permits
WHERE issued_at >= NOW() - INTERVAL '30 days'
ORDER BY issued_at DESC;

-- High-value permits view (>$50k)
CREATE OR REPLACE VIEW gold.high_value_permits AS
SELECT 
    id,
    permit_id,
    issued_at,
    address,
    city,
    county,
    description,
    permit_type,
    applicant_name,
    contractor_name,
    valuation,
    geom
FROM gold.permits
WHERE valuation > 50000
ORDER BY valuation DESC;

-- ===================================================================
-- COMMENTS FOR DOCUMENTATION
-- ===================================================================

COMMENT ON SCHEMA raw IS 'Raw extracted data from external sources';
COMMENT ON SCHEMA bronze IS 'Basic normalized data with consistent formats';
COMMENT ON SCHEMA silver IS 'Business logic applied, enriched data';
COMMENT ON SCHEMA gold IS 'Production-ready, analytics-optimized data';
COMMENT ON SCHEMA meta IS 'Metadata, configuration, and pipeline state';

COMMENT ON TABLE meta.sources IS 'Registry of all data sources and their configuration';
COMMENT ON TABLE meta.ingest_state IS 'Tracking state for data ingestion pipeline';
COMMENT ON TABLE gold.permits IS 'Building permits from all Texas jurisdictions';
COMMENT ON TABLE gold.violations IS 'Code violations and enforcement actions';
COMMENT ON TABLE gold.inspections IS 'Building inspections and results';
COMMENT ON TABLE gold.bids IS 'Government procurement opportunities';
COMMENT ON TABLE gold.awards IS 'Awarded government contracts';
COMMENT ON TABLE gold.contractors IS 'Licensed contractors from TDLR and local sources';
COMMENT ON TABLE gold.lead_scores IS 'ML-generated lead scores with versioning';

-- Migration completed successfully
SELECT 'Database schema 2025-setup.sql applied successfully' AS status;