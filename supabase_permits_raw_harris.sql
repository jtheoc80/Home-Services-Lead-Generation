-- SQL for Supabase to create public.permits_raw_harris
-- Exact specification as required

create table if not exists public.permits_raw_harris (
  event_id bigint primary key,
  permit_number text,
  permit_name text,
  app_type text,
  issue_date timestamptz,
  project_number text,
  full_address text,
  street_number numeric,
  street_name text,
  status text,
  raw jsonb,
  created_at timestamptz default now()
);

create index if not exists idx_permits_harris_issue_date on public.permits_raw_harris(issue_date desc);