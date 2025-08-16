-- ====== PERMITS DEDUPE ======
-- First, add missing columns if they don't exist
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS permit_id TEXT;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS permit_no TEXT;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS jurisdiction TEXT;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS category TEXT;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS value NUMERIC;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS state TEXT;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS applied_date TIMESTAMPTZ;
ALTER TABLE public.permits ADD COLUMN IF NOT EXISTS scraped_at TIMESTAMPTZ;

-- Backfill permit_id from existing permit_number or id
UPDATE public.permits 
SET permit_id = COALESCE(permit_number, id::text)
WHERE permit_id IS NULL;

-- Backfill permit_no from permit_number  
UPDATE public.permits 
SET permit_no = permit_number
WHERE permit_no IS NULL AND permit_number IS NOT NULL;

-- Backfill description from work_description
UPDATE public.permits 
SET description = work_description
WHERE description IS NULL AND work_description IS NOT NULL;

-- Backfill value from valuation
UPDATE public.permits 
SET value = valuation
WHERE value IS NULL AND valuation IS NOT NULL;

-- Backfill applied_date from application_date
UPDATE public.permits 
SET applied_date = application_date
WHERE applied_date IS NULL AND application_date IS NOT NULL;

create unique index if not exists uq_permits_source_permit_id
  on public.permits (source, permit_id)
  where permit_id is not null;

create unique index if not exists uq_permits_source_src_rec
  on public.permits (source, source_record_id)
  where source_record_id is not null;

-- Helpful indexes
create index if not exists permits_issued_idx  on public.permits (issued_date desc nulls last);
create index if not exists permits_created_idx on public.permits (created_at desc nulls last);

-- ====== LEADS FK + UNIQUENESS ======
-- First ensure permit_id column exists in leads table and is the right type
DO $$ 
BEGIN
    -- Check if permit_id exists and is UUID type (for FK to permits.id)
    IF EXISTS (SELECT 1 FROM information_schema.columns 
               WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'permit_id' AND data_type = 'text') THEN
        -- Convert text permit_id to UUID to match permits.id
        ALTER TABLE public.leads ALTER COLUMN permit_id TYPE UUID USING permit_id::UUID;
    ELSIF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                     WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'permit_id') THEN
        -- Add permit_id column as UUID
        ALTER TABLE public.leads ADD COLUMN permit_id UUID;
    END IF;
END $$;

alter table public.leads
  add constraint if not exists leads_permit_fk
  foreign key (permit_id) references public.permits(id) on delete set null;

create unique index if not exists leads_permit_unique
  on public.leads (permit_id)
  where permit_id is not null;

-- ====== RPC: UPSERT PERMIT ======
create or replace function public.upsert_permit(p jsonb)
returns uuid
language plpgsql
as $$
declare
  rid uuid;
  v_permit_id text := coalesce(p->>'permit_id', p->>'permit_no', p->>'permit_number', p->>'source_record_id');
begin
  insert into public.permits (
    source, source_record_id, permit_id, jurisdiction, county, permit_no, permit_number,
    permit_type, permit_class, category, status, description, work_description, value, valuation,
    address, city, state, zipcode, latitude, longitude,
    applied_date, application_date, issued_date, scraped_at, raw_data, created_at, updated_at
  )
  values (
    p->>'source', p->>'source_record_id', v_permit_id, p->>'jurisdiction', p->>'county', 
    coalesce(p->>'permit_no', p->>'permit_number'), p->>'permit_number',
    p->>'permit_type', p->>'permit_class', p->>'category', p->>'status', 
    coalesce(p->>'description', p->>'work_description'), p->>'work_description',
    nullif(p->>'value','')::numeric, nullif(p->>'valuation','')::numeric,
    p->>'address', p->>'city', coalesce(p->>'state','TX'), p->>'zipcode',
    nullif(p->>'latitude','')::double precision, nullif(p->>'longitude','')::double precision,
    nullif(p->>'applied_date','')::timestamptz, nullif(p->>'application_date','')::timestamptz,
    nullif(p->>'issued_date','')::timestamptz,
    coalesce(nullif(p->>'scraped_at','')::timestamptz, now()), p, now(), now()
  )
  on conflict (source, source_record_id) do update set
    permit_id   = coalesce(excluded.permit_id, public.permits.permit_id),
    jurisdiction= excluded.jurisdiction,
    county      = excluded.county,
    permit_no   = excluded.permit_no,
    permit_number = excluded.permit_number,
    permit_type = excluded.permit_type,
    permit_class = excluded.permit_class,
    category    = excluded.category,
    status      = excluded.status,
    description = excluded.description,
    work_description = excluded.work_description,
    value       = excluded.value,
    valuation   = excluded.valuation,
    address     = excluded.address,
    city        = excluded.city,
    state       = excluded.state,
    zipcode     = excluded.zipcode,
    latitude    = excluded.latitude,
    longitude   = excluded.longitude,
    applied_date= excluded.applied_date,
    application_date = excluded.application_date,
    issued_date = excluded.issued_date,
    scraped_at  = excluded.scraped_at,
    raw_data    = excluded.raw_data,
    updated_at  = now()
  returning id into rid;

  return rid;
end;
$$;

-- ====== TRIGGER: PERMIT → LEAD ======
-- Ensure leads table has required columns
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS name TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS trade TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS county TEXT;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'new';
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS value NUMERIC;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS lead_score INTEGER;
ALTER TABLE public.leads ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();

create or replace function public.create_lead_from_permit()
returns trigger
language plpgsql
as $$
declare
  v_name text;
  v_trade text;
begin
  v_name  := coalesce(
    nullif(new.description,''), 
    nullif(new.work_description,''),
    'Permit ' || coalesce(new.permit_no, new.permit_number, new.permit_id, '(no #)')
  );
  v_trade := coalesce(nullif(new.permit_type,''), nullif(new.category,''), nullif(new.permit_class,''));

  insert into public.leads (permit_id, name, trade, county, status, value, lead_score, created_at)
  values (
    new.id, v_name, v_trade, nullif(new.county,''), coalesce(nullif(new.status,''),'New'),
    coalesce(new.value, new.valuation), 75, coalesce(new.issued_date, now())
  )
  on conflict (permit_id) do nothing;

  return new;
end;
$$;

drop trigger if exists trg_lead_from_permit on public.permits;
create trigger trg_lead_from_permit
after insert on public.permits
for each row execute function public.create_lead_from_permit();

-- ====== BACKFILL MISSING LEADS ======
insert into public.leads (permit_id, name, trade, county, status, value, lead_score, created_at)
select p.id,
       coalesce(
         nullif(p.description,''), 
         nullif(p.work_description,''),
         'Permit ' || coalesce(p.permit_no, p.permit_number, p.permit_id, '(no #)')
       ) as name,
       coalesce(nullif(p.permit_type,''), nullif(p.category,''), nullif(p.permit_class,'')) as trade,
       nullif(p.county,'') as county,
       coalesce(nullif(p.status,''),'New') as status,
       coalesce(p.value, p.valuation),
       75,
       coalesce(p.issued_date, p.created_at, now())
from public.permits p
left join public.leads l on l.permit_id = p.id
where l.permit_id is null;

-- ====== DEV READ POLICIES (optional; remove if you require auth) ======
alter table public.leads enable row level security;
drop policy if exists leads_read_anon_dev on public.leads;
create policy leads_read_anon_dev on public.leads for select to anon using (true);

alter table public.permits enable row level security;
drop policy if exists permits_read_anon_dev on public.permits;
create policy permits_read_anon_dev on public.permits for select to anon using (true);