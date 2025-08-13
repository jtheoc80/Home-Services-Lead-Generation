-- TX Permits Integration Schema - Idempotent Migration
-- Creates gold.permits schema with PostGIS support for normalized permit data

-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;
CREATE SCHEMA IF NOT EXISTS meta;

-- Create sources metadata table
CREATE TABLE IF NOT EXISTS meta.sources(
  source_id text primary key,
  kind text,
  endpoint text,
  entity text,
  updated_field text,
  primary_key text,
  cadence text,
  license text,
  provenance_url text,
  created_at timestamptz default now()
);

-- Create ingest state tracking table
CREATE TABLE IF NOT EXISTS meta.ingest_state(
  source_id text primary key,
  last_run_at timestamptz,
  last_updated_seen timestamptz,
  last_status text
);

-- Create main gold permits table
CREATE TABLE IF NOT EXISTS gold.permits(
  -- Source and identity
  source_id text not null,
  permit_id text not null,
  jurisdiction text,
  city text,
  county text,
  state text default 'TX',
  
  -- Permit details
  status text,
  permit_type text,
  subtype text,
  work_class text,
  description text,
  
  -- Dates
  applied_at timestamptz,
  issued_at timestamptz,
  finaled_at timestamptz,
  
  -- Location
  address_full text,
  postal_code text,
  parcel_id text,
  
  -- Project details
  valuation numeric,
  
  -- Parties
  contractor_name text,
  contractor_license text,
  
  -- Geography
  latitude double precision,
  longitude double precision,
  geom geometry(Point,4326),
  
  -- Links and metadata
  url text,
  provenance jsonb default '{}'::jsonb,
  record_hash text not null,
  updated_at timestamptz default now(),
  
  primary key (source_id, permit_id)
);

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_permits_issued_brin ON gold.permits USING brin(issued_at);
CREATE INDEX IF NOT EXISTS idx_permits_geom ON gold.permits USING gist(geom);
CREATE INDEX IF NOT EXISTS idx_permits_city_county ON gold.permits(city, county);
CREATE INDEX IF NOT EXISTS idx_permits_type ON gold.permits(permit_type);
CREATE INDEX IF NOT EXISTS idx_permits_status ON gold.permits(status);
CREATE INDEX IF NOT EXISTS idx_permits_jurisdiction ON gold.permits(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_permits_record_hash ON gold.permits(record_hash);

-- Create lead scores table for scoring v0 integration
CREATE TABLE IF NOT EXISTS gold.lead_scores(
  lead_id text not null,
  version text not null,
  score integer not null check (score >= 0 and score <= 100),
  reasons text[] not null,
  created_at timestamptz default now(),
  primary key (lead_id, version)
);

-- Index for lead scores
CREATE INDEX IF NOT EXISTS idx_lead_scores_score ON gold.lead_scores(score desc);
CREATE INDEX IF NOT EXISTS idx_lead_scores_created_at ON gold.lead_scores(created_at desc);

-- Insert initial sources metadata
INSERT INTO meta.sources (source_id, kind, endpoint, entity, updated_field, primary_key, cadence, license, provenance_url) VALUES
  ('dallas_permits', 'socrata', 'https://www.dallasopendata.com/resource/e7gq-4sah.json', 'permits', 'last_update_date', 'permit_number', 'daily', 'public', 'https://www.dallasopendata.com/dataset/e7gq-4sah'),
  ('austin_permits', 'socrata', 'https://data.austintexas.gov/resource/3syk-w9eu.json', 'permits', 'last_update', 'permit_num', 'daily', 'public', 'https://data.austintexas.gov/d/3syk-w9eu'),
  ('arlington_permits', 'arcgis', 'https://gis2.arlingtontx.gov/agsext2/rest/services/OpenData/OD_Property/MapServer/1', 'permits', 'EditDate', 'OBJECTID', 'daily', 'public', 'https://gis2.arlingtontx.gov/open-data')
ON CONFLICT (source_id) DO UPDATE SET
  kind = EXCLUDED.kind,
  endpoint = EXCLUDED.endpoint,
  entity = EXCLUDED.entity,
  updated_field = EXCLUDED.updated_field,
  primary_key = EXCLUDED.primary_key,
  cadence = EXCLUDED.cadence,
  license = EXCLUDED.license,
  provenance_url = EXCLUDED.provenance_url;

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA gold TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA meta TO your_app_user;