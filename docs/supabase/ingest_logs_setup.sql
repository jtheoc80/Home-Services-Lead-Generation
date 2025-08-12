-- Create ingest_logs table for tracking lead processing pipeline
-- This table stores audit logs for lead ingestion and processing stages

create table if not exists public.ingest_logs(
  id bigserial primary key,
  created_at timestamptz default now(),
  trace_id uuid,
  stage text not null,      -- e.g., "validate", "db_insert", "api_request"
  ok boolean not null,
  details jsonb
);

-- Create index for efficient trace_id lookups
create index if not exists idx_ingest_logs_trace on public.ingest_logs(trace_id);

-- Create additional indexes for performance
create index if not exists idx_ingest_logs_created_at on public.ingest_logs(created_at);
create index if not exists idx_ingest_logs_stage on public.ingest_logs(stage);
create index if not exists idx_ingest_logs_ok on public.ingest_logs(ok);

-- Enable Row Level Security (RLS) on ingest_logs
alter table public.ingest_logs enable row level security;

-- Allow service role to insert and select all ingest_logs (for backend processing)
create policy "Service role full access to ingest_logs"
  on public.ingest_logs
  for all
  to service_role
  using (true)
  with check (true);

-- Allow authenticated users to read ingest_logs (for debugging)
create policy "Authenticated users can read ingest_logs"
  on public.ingest_logs
  for select
  to authenticated
  using (true);

-- Add comment for documentation
comment on table public.ingest_logs is 'Audit trail for lead ingestion and processing pipeline';
comment on column public.ingest_logs.trace_id is 'UUID to track a lead processing session across multiple stages';
comment on column public.ingest_logs.stage is 'Processing stage: validate, db_insert, api_request, etc.';
comment on column public.ingest_logs.ok is 'Whether this stage completed successfully';
comment on column public.ingest_logs.details is 'JSON details about the stage processing (errors, metadata, etc.)';

-- Insert a test record to verify the setup
insert into public.ingest_logs (trace_id, stage, ok, details)
values (gen_random_uuid(), 'setup_test', true, '{"message": "ingest_logs table created successfully"}');

-- Verify the setup
select 'ingest_logs table setup completed successfully!' as message;