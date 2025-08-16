-- =====================================================================
-- Companion Migration: Add missing columns & backfill for permit->lead pipeline
-- Date: 2025-08-16
-- Purpose: Ensure all columns referenced by the updated create_lead_from_permit() trigger exist
--           and populate canonical identifiers + service/trade + metadata scaffolding.
-- Safe to run multiple times (idempotent guards used).
-- =====================================================================

-- Enable required extension (idempotent)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =============================================
-- PERMITS TABLE ENHANCEMENTS
-- =============================================
DO $$
BEGIN
  -- Add textual canonical permit_id column if missing
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='permit_id'
  ) THEN
    ALTER TABLE public.permits ADD COLUMN permit_id TEXT;
  END IF;

  -- Participant / classification fields
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='applicant') THEN
    ALTER TABLE public.permits ADD COLUMN applicant TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='owner') THEN
    ALTER TABLE public.permits ADD COLUMN owner TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='contractor_name') THEN
    ALTER TABLE public.permits ADD COLUMN contractor_name TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='work_class') THEN
    ALTER TABLE public.permits ADD COLUMN work_class TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='work_description') THEN
    ALTER TABLE public.permits ADD COLUMN work_description TEXT;
  END IF;

  -- Raw metadata & provenance
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='raw_data') THEN
    ALTER TABLE public.permits ADD COLUMN raw_data JSONB DEFAULT '{}'::jsonb;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='provenance') THEN
    ALTER TABLE public.permits ADD COLUMN provenance JSONB DEFAULT '{}'::jsonb;
  END IF;

  -- Lifecycle fields
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='finaled_at') THEN
    ALTER TABLE public.permits ADD COLUMN finaled_at TIMESTAMPTZ;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='expiration_date') THEN
    ALTER TABLE public.permits ADD COLUMN expiration_date TIMESTAMPTZ;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='application_date') THEN
    ALTER TABLE public.permits ADD COLUMN application_date TIMESTAMPTZ;
  END IF;

  -- Hash for change detection
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='record_hash') THEN
    ALTER TABLE public.permits ADD COLUMN record_hash TEXT;
  END IF;
END $$;

-- Backfill application_date from applied_date if present
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='applied_date')
     AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='permits' AND column_name='application_date') THEN
    UPDATE public.permits SET application_date = applied_date
      WHERE application_date IS NULL AND applied_date IS NOT NULL;
  END IF;
END $$;

-- Populate permit_id from existing columns if null
UPDATE public.permits p
SET permit_id = COALESCE(p.permit_id, NULLIF(p.permit_no,''), NULLIF(p.source_record_id,''))
WHERE permit_id IS NULL;

-- Unique index on (source, permit_id) (partial) for canonical uniqueness
CREATE UNIQUE INDEX IF NOT EXISTS uq_permits_source_permit_id
  ON public.permits(source, permit_id)
  WHERE permit_id IS NOT NULL;

-- Optional: compute record_hash (simple example using md5 of concatenated fields)
UPDATE public.permits p
SET record_hash = md5(
      COALESCE(p.source,'') || '|' || COALESCE(p.permit_id,'') || '|' || COALESCE(p.status,'') || '|' || COALESCE(p.value::text,'') || '|' || COALESCE(p.issued_date::text,'')
    )
WHERE p.record_hash IS NULL;

-- =============================================
-- LEADS TABLE ENHANCEMENTS
-- =============================================
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='leads' AND column_name='service') THEN
    ALTER TABLE public.leads ADD COLUMN service TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='leads' AND column_name='trade') THEN
    ALTER TABLE public.leads ADD COLUMN trade TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='leads' AND column_name='external_permit_id') THEN
    ALTER TABLE public.leads ADD COLUMN external_permit_id TEXT;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='leads' AND column_name='metadata') THEN
    ALTER TABLE public.leads ADD COLUMN metadata JSONB DEFAULT '{}'::jsonb;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='leads' AND column_name='source') THEN
    ALTER TABLE public.leads ADD COLUMN source TEXT;
  END IF;
END $$;

-- Sync service/trade if only one populated
UPDATE public.leads SET service = trade WHERE service IS NULL AND trade IS NOT NULL;
UPDATE public.leads SET trade = service WHERE trade IS NULL AND service IS NOT NULL;

-- Backfill external_permit_id via join on permits (assuming leads.permit_id is UUID FK)
UPDATE public.leads l
SET external_permit_id = p.permit_id
FROM public.permits p
WHERE l.permit_id = p.id
  AND l.external_permit_id IS NULL
  AND p.permit_id IS NOT NULL;

-- Unique index on external_permit_id (partial) to prevent duplicates when present
CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_external_permit_id
  ON public.leads(external_permit_id)
  WHERE external_permit_id IS NOT NULL;

-- Optional uniqueness on leads.permit_id if 1:1 expected
CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_permit_uuid ON public.leads(permit_id);

-- =============================================
-- VERIFICATION QUERIES (commented)
-- =============================================
-- SELECT permit_id, applicant, owner, work_class FROM public.permits ORDER BY created_at DESC LIMIT 3;
-- SELECT id, service, trade, external_permit_id, source FROM public.leads ORDER BY created_at DESC LIMIT 3;
-- =============================================
