-- Temporary RLS policies for testing
-- These policies allow anonymous users to insert and select leads for E2E testing
-- IMPORTANT: Remove these policies after testing and replace with authenticated-only policies

-- Drop existing temporary policies if they exist
drop policy if exists "temp_anon_insert_leads" on public.leads;
drop policy if exists "temp_anon_select_leads" on public.leads;

-- Enable RLS on leads table (if not already enabled)
alter table public.leads enable row level security;

-- TEMPORARY: Allow anonymous users to insert leads (for E2E testing)
create policy "temp_anon_insert_leads"
  on public.leads
  for insert
  to anon
  with check (true);

-- TEMPORARY: Allow anonymous users to select all leads (for E2E testing)
create policy "temp_anon_select_leads"
  on public.leads
  for select
  to anon
  using (true);

-- Verify policies are active
select 'Temporary anon RLS policies created successfully! Remember to remove after testing.' as message;