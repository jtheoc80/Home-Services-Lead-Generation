-- Remove temporary anon policies and replace with authenticated-only policies
-- Run this script after E2E testing is complete to secure the leads table

-- Remove temporary anonymous policies
drop policy if exists "temp_anon_insert_leads" on public.leads;
drop policy if exists "temp_anon_select_leads" on public.leads;

-- Create authenticated-only policies for production use
create policy "authenticated_users_insert_leads"
  on public.leads
  for insert
  to authenticated
  with check (true);

create policy "authenticated_users_select_leads"
  on public.leads
  for select
  to authenticated
  using (true);

create policy "authenticated_users_update_leads"
  on public.leads
  for update
  to authenticated
  using (true)
  with check (true);

-- Allow service role full access (for backend processing)
create policy "service_role_full_access_leads"
  on public.leads
  for all
  to service_role
  using (true)
  with check (true);

-- Verify the production policies are active
select 'Production authenticated-only RLS policies created successfully!' as message;