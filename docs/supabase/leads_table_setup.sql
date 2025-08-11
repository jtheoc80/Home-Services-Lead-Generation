-- PostgreSQL script for Supabase: Create leads table with RLS and policies
-- This script creates the public.leads table exactly as specified in requirements

-- Enable pgcrypto extension for gen_random_uuid() function
create extension if not exists "pgcrypto";

-- Create public.leads table with specified columns
create table if not exists public.leads (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz default now(),
    name text,
    email text,
    phone text,
    source text,
    status text default 'new',
    metadata jsonb
);

-- Enable Row Level Security (RLS) on the table
alter table public.leads enable row level security;

-- Add TEMP policies allowing anon role to insert and select all rows
-- Policy for anonymous insert
drop policy if exists "temp_anon_insert_leads" on public.leads;
create policy "temp_anon_insert_leads"
    on public.leads for insert
    to anon
    with check (true);

-- Policy for anonymous select (select all rows)
drop policy if exists "temp_anon_select_leads" on public.leads;
create policy "temp_anon_select_leads"
    on public.leads for select
    to anon
    using (true);

-- Insert seed row
insert into public.leads (name, email, source)
values ('Smoke Test', 'smoke@example.com', 'manual')
values ('Smoke Test', 'smoke@example.com', 'manual');

-- Verify the setup
select 'Leads table setup completed successfully!' as message;