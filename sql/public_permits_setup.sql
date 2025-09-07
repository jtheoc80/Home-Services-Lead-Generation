-- PostgreSQL script for Supabase: Create public.permits table for TX permit ingest
-- This script creates the public.permits table for ingesting permit data from TX sources
-- with unique constraint on (source, source_record_id) and optimized indexes

-- Enable PostGIS extension for geometry support
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create public.permits table for TX permit ingestion
CREATE TABLE IF NOT EXISTS public.permits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Source identification with unique constraint
  source TEXT NOT NULL, -- 'austin', 'houston', 'dallas'
  source_record_id TEXT NOT NULL, -- Original record ID from source
  
  -- Core permit information
  permit_number TEXT,
  issued_date TIMESTAMPTZ,
  application_date TIMESTAMPTZ,
  expiration_date TIMESTAMPTZ,
  
  -- Work and permit classification
  permit_type TEXT,
  permit_class TEXT,
  work_description TEXT,
  trade TEXT DEFAULT 'General',
  
  -- Location information
  address TEXT,
  city TEXT,
  county TEXT,
  zipcode TEXT,
  latitude NUMERIC,
  longitude NUMERIC,
  geom GEOMETRY(POINT, 4326), -- PostGIS geometry column
  
  -- Financial details
  valuation NUMERIC,
  square_feet INTEGER,
  
  -- People and entities
  applicant_name TEXT,
  contractor_name TEXT,
  owner_name TEXT,
  
  -- Status
  status TEXT,
  
  -- Raw data preservation
  raw_data JSONB,
  
  -- Metadata
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Unique constraint on source and source record ID
  UNIQUE(source, source_record_id)
);

-- Create helpful indexes for performance
CREATE INDEX IF NOT EXISTS idx_permits_source ON public.permits(source);
CREATE INDEX IF NOT EXISTS idx_permits_issued_date ON public.permits(issued_date);
CREATE INDEX IF NOT EXISTS idx_permits_city ON public.permits(city);
CREATE INDEX IF NOT EXISTS idx_permits_county ON public.permits(county);
CREATE INDEX IF NOT EXISTS idx_permits_valuation ON public.permits(valuation);
CREATE INDEX IF NOT EXISTS idx_permits_status ON public.permits(status);
CREATE INDEX IF NOT EXISTS idx_permits_trade ON public.permits(trade);
CREATE INDEX IF NOT EXISTS idx_permits_created_at ON public.permits(created_at);

-- Spatial index for geometry queries
CREATE INDEX IF NOT EXISTS idx_permits_geom ON public.permits USING GIST(geom);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_permits_source_date ON public.permits(source, issued_date);

-- Function to update geometry from lat/lng when they are provided
CREATE OR REPLACE FUNCTION update_permits_geom_from_coordinates()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update geometry and updated_at
CREATE OR REPLACE TRIGGER trigger_permits_update_geom
  BEFORE INSERT OR UPDATE ON public.permits
  FOR EACH ROW
  EXECUTE FUNCTION update_permits_geom_from_coordinates();

-- Reusable function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update the updated_at timestamp
CREATE OR REPLACE TRIGGER set_updated_at
  BEFORE UPDATE ON public.permits
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Composite index for sorting by issued_date then created_at as fallback
CREATE INDEX IF NOT EXISTS idx_permits_issued_date_created_at ON public.permits(issued_date DESC, created_at DESC);

-- Create RPC function for upsert_permit
CREATE OR REPLACE FUNCTION public.upsert_permit(permit_data JSONB)
RETURNS TABLE(id UUID, action TEXT) AS $$
DECLARE
  permit_id UUID;
  permit_action TEXT;
  source_val TEXT;
  source_record_id_val TEXT;
BEGIN
  -- Extract required fields
  source_val := permit_data->>'source';
  source_record_id_val := permit_data->>'source_record_id';
  
  -- Validate required fields
  IF source_val IS NULL OR source_record_id_val IS NULL THEN
    RAISE EXCEPTION 'source and source_record_id are required fields';
  END IF;
  
  -- Attempt to update existing record
  UPDATE public.permits SET
    permit_number = permit_data->>'permit_number',
    issued_date = CASE 
      WHEN permit_data->>'issued_date' IS NOT NULL 
      THEN (permit_data->>'issued_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    application_date = CASE 
      WHEN permit_data->>'application_date' IS NOT NULL 
      THEN (permit_data->>'application_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    expiration_date = CASE 
      WHEN permit_data->>'expiration_date' IS NOT NULL 
      THEN (permit_data->>'expiration_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    permit_type = permit_data->>'permit_type',
    permit_class = permit_data->>'permit_class',
    work_description = permit_data->>'work_description',
    address = permit_data->>'address',
    city = permit_data->>'city',
    county = permit_data->>'county',
    zipcode = permit_data->>'zipcode',
    latitude = CASE 
      WHEN permit_data->>'latitude' IS NOT NULL 
      THEN (permit_data->>'latitude')::NUMERIC 
      ELSE NULL 
    END,
    longitude = CASE 
      WHEN permit_data->>'longitude' IS NOT NULL 
      THEN (permit_data->>'longitude')::NUMERIC 
      ELSE NULL 
    END,
    valuation = CASE 
      WHEN permit_data->>'valuation' IS NOT NULL 
      THEN (permit_data->>'valuation')::NUMERIC 
      ELSE NULL 
    END,
    square_feet = CASE 
      WHEN permit_data->>'square_feet' IS NOT NULL 
      THEN (permit_data->>'square_feet')::INTEGER 
      ELSE NULL 
    END,
    applicant_name = permit_data->>'applicant_name',
    contractor_name = permit_data->>'contractor_name',
    owner_name = permit_data->>'owner_name',
    status = permit_data->>'status',
    raw_data = permit_data,
    updated_at = NOW()
  WHERE source = source_val AND source_record_id = source_record_id_val
  RETURNING public.permits.id INTO permit_id;
  
  -- If update affected a row, return it
  IF permit_id IS NOT NULL THEN
    permit_action := 'updated';
    RETURN QUERY SELECT permit_id, permit_action;
    RETURN;
  END IF;
  
  -- Otherwise, insert new record
  INSERT INTO public.permits (
    source,
    source_record_id,
    permit_number,
    issued_date,
    application_date,
    expiration_date,
    permit_type,
    permit_class,
    work_description,
    address,
    city,
    county,
    zipcode,
    latitude,
    longitude,
    valuation,
    square_feet,
    applicant_name,
    contractor_name,
    owner_name,
    status,
    raw_data
  ) VALUES (
    source_val,
    source_record_id_val,
    permit_data->>'permit_number',
    CASE 
      WHEN permit_data->>'issued_date' IS NOT NULL 
      THEN (permit_data->>'issued_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    CASE 
      WHEN permit_data->>'application_date' IS NOT NULL 
      THEN (permit_data->>'application_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    CASE 
      WHEN permit_data->>'expiration_date' IS NOT NULL 
      THEN (permit_data->>'expiration_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    permit_data->>'permit_type',
    permit_data->>'permit_class',
    permit_data->>'work_description',
    permit_data->>'address',
    permit_data->>'city',
    permit_data->>'county',
    permit_data->>'zipcode',
    CASE 
      WHEN permit_data->>'latitude' IS NOT NULL 
      THEN (permit_data->>'latitude')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN permit_data->>'longitude' IS NOT NULL 
      THEN (permit_data->>'longitude')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN permit_data->>'valuation' IS NOT NULL 
      THEN (permit_data->>'valuation')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN permit_data->>'square_feet' IS NOT NULL 
      THEN (permit_data->>'square_feet')::INTEGER 
      ELSE NULL 
    END,
    permit_data->>'applicant_name',
    permit_data->>'contractor_name',
    permit_data->>'owner_name',
    permit_data->>'status',
    permit_data
  ) RETURNING public.permits.id INTO permit_id;
  
  permit_action := 'inserted';
  RETURN QUERY SELECT permit_id, permit_action;
END;
$$ LANGUAGE plpgsql;

-- Add table comments for documentation
COMMENT ON TABLE public.permits IS 'Texas permits ingestion table for Austin, Houston, Dallas data with unique source constraints';
COMMENT ON COLUMN public.permits.source IS 'Source system identifier (austin, houston, dallas)';
COMMENT ON COLUMN public.permits.source_record_id IS 'Original record identifier from source system';
COMMENT ON FUNCTION public.upsert_permit(JSONB) IS 'Idempotent upsert function for permit records using source and source_record_id';

-- Success message
SELECT 'Public permits table and upsert function created successfully!' AS message;