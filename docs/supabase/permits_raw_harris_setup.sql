-- PostgreSQL script for Supabase: Create permits_raw_harris table for raw permit ingest
-- This script creates the public.permits_raw_harris table for ingesting raw Harris County permit data
-- 
-- Purpose: Raw ingest table for Harris County building permits
-- - High-performance ingestion with minimal constraints
-- - Fast indexing for date-based queries
-- - RLS disabled for service-role ingest operations
-- - JSONB raw field for storing original permit data

-- Create permits_raw_harris table with specified schema
create table if not exists public.permits_raw_harris (
  event_id bigint primary key,
  permit_number text,
  permit_name text,
  app_type text,
  issue_date timestamptz,
  project_number text,
  full_address text,
  street_number text,
  street_name text,
  status text,
  raw jsonb,
  created_at timestamptz default now()
);

-- Create fast index for date-based queries (descending for recent-first ordering)
create index if not exists idx_permits_harris_issue_date on public.permits_raw_harris(issue_date desc);

-- Additional indexes for common query patterns
create index if not exists idx_permits_harris_status on public.permits_raw_harris(status);
create index if not exists idx_permits_harris_permit_number on public.permits_raw_harris(permit_number);
create index if not exists idx_permits_harris_created_at on public.permits_raw_harris(created_at desc);

-- Disable Row Level Security for raw ingest table
-- This table is for service-role ingest only, not end-user access
alter table public.permits_raw_harris disable row level security;

-- Add table and column comments for documentation
comment on table public.permits_raw_harris is 'Raw ingest table for Harris County building permits - service-role access only';
comment on column public.permits_raw_harris.event_id is 'Unique permit event identifier from Harris County system';
comment on column public.permits_raw_harris.permit_number is 'Official permit number assigned by Harris County';
comment on column public.permits_raw_harris.permit_name is 'Descriptive name/title of the permit';
comment on column public.permits_raw_harris.app_type is 'Application type (e.g., building, electrical, plumbing)';
comment on column public.permits_raw_harris.issue_date is 'Date the permit was issued';
comment on column public.permits_raw_harris.project_number is 'Internal project number if applicable';
comment on column public.permits_raw_harris.full_address is 'Complete address of the permitted work';
comment on column public.permits_raw_harris.street_number is 'Numeric portion of street address';
comment on column public.permits_raw_harris.street_name is 'Street name portion of address';
comment on column public.permits_raw_harris.status is 'Current permit status (issued, expired, completed, etc.)';
comment on column public.permits_raw_harris.raw is 'Original raw permit data in JSONB format for reference';
comment on column public.permits_raw_harris.created_at is 'Timestamp when record was inserted into this table';

-- Success message
select 'Harris County permits raw ingest table created successfully!' as message;