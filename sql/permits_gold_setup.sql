-- PostgreSQL script for Supabase: Create permits_gold table for normalized Texas permit data
-- This script creates the public.permits_gold table for normalized permit data across all Texas jurisdictions
-- 
-- Purpose: Normalized permit data table with common schema for all Texas cities
-- - Standardized columns across Dallas, Austin, Arlington, Houston, Harris County
-- - Geospatial support with PostGIS geometry
-- - Optimized for analytics and lead generation
-- - RLS for secure user access

-- Enable PostGIS extension for geometry support
create extension if not exists postgis;

-- Create permits_gold table with normalized schema
create table if not exists public.permits_gold (
  id uuid primary key default gen_random_uuid(),
  
  -- Source identification
  jurisdiction text not null,
  source_type text not null, -- 'socrata', 'arcgis', 'tpia_csv'
  permit_id text not null,
  source_permit_number text,
  
  -- Core permit information
  issued_date timestamptz,
  application_date timestamptz,
  expiration_date timestamptz,
  
  -- Work classification
  work_type text, -- Normalized work type (residential, commercial, industrial)
  permit_category text, -- Specific permit category
  work_description text,
  
  -- Location
  address text,
  latitude numeric,
  longitude numeric,
  geom geometry(POINT, 4326), -- PostGIS geometry column
  
  -- Financial and project details
  valuation numeric, -- Project valuation/estimated cost
  project_value_band text, -- Categorized value bands for analytics
  
  -- People and entities
  applicant_name text,
  contractor_name text,
  property_owner text,
  
  -- Status and lifecycle
  permit_status text,
  current_status text,
  
  -- Raw data preservation
  raw_data jsonb, -- Original source data
  source_url text,
  
  -- Metadata
  created_at timestamptz default now(),
  updated_at timestamptz default now(),
  ingested_at timestamptz default now(),
  
  -- Composite unique constraint across jurisdiction and permit
  unique(jurisdiction, permit_id)
);

-- Create optimized indexes for common query patterns
create index if not exists idx_permits_gold_issued_date on public.permits_gold(issued_date desc);
create index if not exists idx_permits_gold_jurisdiction on public.permits_gold(jurisdiction);
create index if not exists idx_permits_gold_work_type on public.permits_gold(work_type);
create index if not exists idx_permits_gold_valuation on public.permits_gold(valuation) where valuation is not null;
create index if not exists idx_permits_gold_status on public.permits_gold(permit_status);
create index if not exists idx_permits_gold_address on public.permits_gold using gin(to_tsvector('english', address));

-- Geospatial index for location-based queries
create index if not exists idx_permits_gold_geom on public.permits_gold using gist(geom);

-- Composite index for jurisdiction + date queries (common pattern)
create index if not exists idx_permits_gold_jurisdiction_date on public.permits_gold(jurisdiction, issued_date desc);

-- Index for recent permits (analytics use case)
create index if not exists idx_permits_gold_recent on public.permits_gold(created_at desc) 
  where created_at > now() - interval '30 days';

-- Enable Row Level Security
alter table public.permits_gold enable row level security;

-- Create trigger to automatically update the updated_at timestamp
create or replace function update_updated_at_column()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger update_permits_gold_updated_at
  before update on public.permits_gold
  for each row
  execute function update_updated_at_column();

-- Create trigger to automatically populate geometry from lat/lng
create or replace function update_geom_from_coordinates()
returns trigger as $$
begin
  if new.latitude is not null and new.longitude is not null then
    new.geom = st_point(new.longitude, new.latitude, 4326);
  end if;
  return new;
end;
$$ language plpgsql;

create trigger update_permits_gold_geom
  before insert or update on public.permits_gold
  for each row
  execute function update_geom_from_coordinates();

-- Function to normalize work type from various source formats
create or replace function normalize_work_type(work_desc text, permit_type text)
returns text as $$
begin
  -- Convert to lowercase for pattern matching
  work_desc := lower(coalesce(work_desc, ''));
  permit_type := lower(coalesce(permit_type, ''));
  
  -- Residential patterns
  if work_desc ~* 'residential|single.?family|duplex|house|home|addition|renovation|remodel|kitchen|bathroom|garage|deck|porch|fence|pool|shed' 
     or permit_type ~* 'residential|single.?family|duplex' then
    return 'residential';
  end if;
  
  -- Commercial patterns  
  if work_desc ~* 'commercial|office|retail|store|warehouse|industrial|manufacturing|factory'
     or permit_type ~* 'commercial|office|retail|industrial' then
    return 'commercial';
  end if;
  
  -- Multi-family residential
  if work_desc ~* 'apartment|condo|townhouse|multi.?family'
     or permit_type ~* 'apartment|multi.?family' then
    return 'multi_family';
  end if;
  
  -- Infrastructure/utility
  if work_desc ~* 'utility|infrastructure|sewer|water|electrical.?service|gas.?line'
     or permit_type ~* 'utility|infrastructure' then
    return 'infrastructure';
  end if;
  
  -- Default to mixed use if unknown
  return 'mixed_use';
end;
$$ language plpgsql;

-- Function to categorize project values into bands
create or replace function categorize_valuation(val numeric)
returns text as $$
begin
  if val is null then
    return 'unknown';
  elsif val < 1000 then
    return 'under_1k';
  elsif val < 5000 then
    return 'tier_1k_5k';
  elsif val < 15000 then
    return 'tier_5k_15k';
  elsif val < 50000 then
    return 'tier_15k_50k';
  elsif val < 100000 then
    return 'tier_50k_100k';
  elsif val < 250000 then
    return 'tier_100k_250k';
  elsif val < 500000 then
    return 'tier_250k_500k';
  elsif val < 1000000 then
    return 'tier_500k_1m';
  else
    return 'tier_1m_plus';
  end if;
end;
$$ language plpgsql;

-- Add table and column comments for documentation
comment on table public.permits_gold is 'Normalized building permits from all Texas jurisdictions for analytics and lead generation';
comment on column public.permits_gold.jurisdiction is 'Source jurisdiction (dallas, austin, arlington, houston, harris_county)';
comment on column public.permits_gold.source_type is 'Data source type (socrata, arcgis, tpia_csv)';
comment on column public.permits_gold.permit_id is 'Normalized permit identifier';
comment on column public.permits_gold.issued_date is 'Date the permit was issued';
comment on column public.permits_gold.work_type is 'Normalized work type (residential, commercial, etc.)';
comment on column public.permits_gold.valuation is 'Project valuation in USD';
comment on column public.permits_gold.geom is 'PostGIS point geometry for spatial queries';
comment on column public.permits_gold.raw_data is 'Original source data preserved in JSONB format';

-- Create view for analytics with computed columns
create or replace view public.permits_analytics as
select 
  *,
  extract(year from issued_date) as issue_year,
  extract(month from issued_date) as issue_month,
  extract(quarter from issued_date) as issue_quarter,
  date_trunc('month', issued_date) as issue_month_start,
  case 
    when issued_date > now() - interval '30 days' then 'recent'
    when issued_date > now() - interval '90 days' then 'current_quarter'
    when issued_date > now() - interval '365 days' then 'current_year'
    else 'historical'
  end as recency,
  categorize_valuation(valuation) as value_band,
  normalize_work_type(work_description, permit_category) as normalized_work_type
from public.permits_gold
where issued_date is not null;

comment on view public.permits_analytics is 'Analytics view with computed columns for reporting and lead generation';

-- Function to upsert permit data (for API use)
create or replace function upsert_permit(p jsonb)
returns jsonb as $$
declare
  result_id uuid;
  result_row public.permits_gold%rowtype;
begin
  -- Insert or update permit data
  insert into public.permits_gold (
    jurisdiction,
    source_type,
    permit_id,
    source_permit_number,
    issued_date,
    application_date,
    work_type,
    permit_category,
    work_description,
    address,
    latitude,
    longitude,
    valuation,
    applicant_name,
    contractor_name,
    property_owner,
    permit_status,
    current_status,
    raw_data,
    source_url,
    scraped_at
  ) values (
    coalesce(p->>'jurisdiction', p->>'source'),
    coalesce(p->>'source_type', 'api'),
    coalesce(p->>'permit_id', p->>'permit_no', p->>'source_record_id'),
    p->>'permit_no',
    (p->>'issued_date')::timestamptz,
    (p->>'applied_date')::timestamptz,
    normalize_work_type(p->>'description', p->>'permit_type'),
    coalesce(p->>'permit_type', p->>'category'),
    p->>'description',
    coalesce(p->>'address', p->>'address_full'),
    (p->>'latitude')::numeric,
    (p->>'longitude')::numeric,
    (p->>'value')::numeric,
    p->>'applicant_name',
    p->>'contractor_name',
    p->>'property_owner',
    coalesce(p->>'status', p->>'permit_status'),
    coalesce(p->>'status', p->>'current_status'),
    p,
    p->>'source_url',
    coalesce((p->>'scraped_at')::timestamptz, now())
  )
  on conflict (jurisdiction, permit_id)
  do update set
    source_permit_number = excluded.source_permit_number,
    issued_date = excluded.issued_date,
    application_date = excluded.application_date,
    work_type = excluded.work_type,
    permit_category = excluded.permit_category,
    work_description = excluded.work_description,
    address = excluded.address,
    latitude = excluded.latitude,
    longitude = excluded.longitude,
    valuation = excluded.valuation,
    applicant_name = excluded.applicant_name,
    contractor_name = excluded.contractor_name,
    property_owner = excluded.property_owner,
    permit_status = excluded.permit_status,
    current_status = excluded.current_status,
    raw_data = excluded.raw_data,
    source_url = excluded.source_url,
    updated_at = now()
  returning id into result_id;

  -- Get the full row to return
  select * into result_row from public.permits_gold where id = result_id;
  
  -- Return success with the inserted/updated row
  return jsonb_build_object(
    'success', true,
    'id', result_row.id,
    'jurisdiction', result_row.jurisdiction,
    'permit_id', result_row.permit_id,
    'created_at', result_row.created_at,
    'updated_at', result_row.updated_at
  );
exception
  when others then
    -- Return error information
    return jsonb_build_object(
      'success', false,
      'error', sqlerrm,
      'sqlstate', sqlstate
    );
end;
$$ language plpgsql security definer;

comment on function upsert_permit(jsonb) is 'Upsert permit data from API calls with conflict resolution';

-- Success message
select 'Texas permits_gold table, analytics view, and upsert function created successfully!' as message;