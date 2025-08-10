-- SQL to run in Supabase SQL Editor. Creates core tables and starter RLS policies.
create table if not exists public.leads (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  source text,
  name text,
  phone text,
  email text,
  address text,
  city text,
  state text,
  zip text,
  status text default 'new'
);
create table if not exists public.contractors (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  company_name text not null,
  contact_name text,
  email text unique,
  phone text,
  plan text default 'free'
);
create table if not exists public.lead_feedback (
  id bigserial primary key,
  created_at timestamptz not null default now(),
  lead_id bigint references public.leads(id) on delete cascade,
  contractor_id uuid references public.contractors(id) on delete set null,
  vote text check (vote in ('up','down')),
  comment text
);
create table if not exists public.contractor_engagement (
  contractor_id uuid primary key references public.contractors(id) on delete cascade,
  last_activity timestamptz,
  score int default 0
);

alter table public.leads enable row level security;
alter table public.lead_feedback enable row level security;
alter table public.contractors enable row level security;
alter table public.contractor_engagement enable row level security;

-- Optional public insert (remove if only ingesting server-side with service role)
create policy anon_can_insert_leads on public.leads for insert to anon with check (true);

create policy auth_can_read_leads on public.leads for select to authenticated using (true);
create policy auth_insert_feedback on public.lead_feedback for insert to authenticated with check (auth.uid() = contractor_id);
create policy auth_read_own_feedback on public.lead_feedback for select to authenticated using (auth.uid() = contractor_id);
create policy auth_self_select on public.contractors for select to authenticated using (auth.uid() = id);
create policy auth_self_update on public.contractors for update to authenticated using (auth.uid() = id);