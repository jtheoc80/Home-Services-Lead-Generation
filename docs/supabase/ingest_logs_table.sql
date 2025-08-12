-- Create ingest_logs table for tracking lead ingestion stages
-- This table logs each step of the lead processing pipeline

create table if not exists public.ingest_logs (
    id bigserial primary key,
    trace_id uuid not null,
    stage text not null,
    ok boolean not null,
    details jsonb,
    created_at timestamptz not null default now()
);

-- Create index for efficient querying by trace_id
create index if not exists idx_ingest_logs_trace_id on public.ingest_logs(trace_id);
create index if not exists idx_ingest_logs_stage on public.ingest_logs(stage);
create index if not exists idx_ingest_logs_created_at on public.ingest_logs(created_at);

-- Enable Row Level Security (RLS)
alter table public.ingest_logs enable row level security;

-- Allow service role to insert logs (no public access needed)
drop policy if exists "service_role_can_insert_logs" on public.ingest_logs;
create policy "service_role_can_insert_logs"
    on public.ingest_logs for insert
    to service_role
    with check (true);

drop policy if exists "service_role_can_select_logs" on public.ingest_logs;
create policy "service_role_can_select_logs"
    on public.ingest_logs for select
    to service_role
    using (true);

-- Add comments for documentation
comment on table public.ingest_logs is 'Logs each stage of lead ingestion for tracing and debugging';
comment on column public.ingest_logs.trace_id is 'UUID to trace a specific lead through the ingestion pipeline';
comment on column public.ingest_logs.stage is 'Stage name: validate, db_insert, etc.';
comment on column public.ingest_logs.ok is 'Whether the stage completed successfully';
comment on column public.ingest_logs.details is 'Additional details about the stage execution';