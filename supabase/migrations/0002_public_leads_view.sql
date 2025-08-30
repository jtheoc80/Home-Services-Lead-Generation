-- Create public read view for leads (adjust columns to your schema)
create or replace view public.public_leads as
select
  id,
  source_record_id,
  created_at
from permits;

-- Make view invoker-secured so it respects caller's role
alter view public.public_leads set (security_invoker = true);

-- Permit anon SELECT on the view (safe, read-only)
grant usage on schema public to anon;
grant select on public.public_leads to anon;

-- (Optional) tighten base tables; rely on view for reads
-- revoke select on permits from anon;