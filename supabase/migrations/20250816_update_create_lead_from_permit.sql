-- =====================================================================
-- Migration: Update permit → lead trigger function
-- Date: 2025-08-16
-- Purpose:
--   * Robust canonical permit identifier resolution
--   * Graceful handling when certain enrichment columns are absent
--   * Consistent service/trade categorization
--   * Support both legacy (leads.permit_id UUID FK) and new external_permit_id text
--   * Avoid duplicate lead creation (idempotent trigger)
-- =====================================================================

-- Safety: wrap in a transaction when applied via tooling
-- BEGIN;

-- Drop existing trigger and function if they exist (idempotent)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_trigger 
    WHERE tgname = 'trg_lead_from_permit'
      AND tgrelid = 'public.permits'::regclass
  ) THEN
    DROP TRIGGER trg_lead_from_permit ON public.permits;
  END IF;

  IF EXISTS (
    SELECT 1 FROM pg_proc 
    WHERE proname = 'create_lead_from_permit'
      AND pg_function_is_visible(oid)
  ) THEN
    DROP FUNCTION public.create_lead_from_permit();
  END IF;
END $$;

-- =====================================================================
-- Function: create_lead_from_permit()
-- Trigger timing: AFTER INSERT ON public.permits
-- =====================================================================
CREATE OR REPLACE FUNCTION public.create_lead_from_permit()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  -- Canonical identifiers
  v_canonical_permit_id TEXT;
  v_permit_uuid UUID := NEW.id;

  -- Lead core data
  v_lead_name TEXT;
  v_lead_email TEXT;
  v_lead_phone TEXT;
  v_lead_service TEXT;
  v_lead_trade TEXT;
  v_lead_address TEXT;
  v_lead_city TEXT;
  v_lead_state TEXT;
  v_lead_zip TEXT;
  v_lead_county TEXT;
  v_lead_value NUMERIC;
  v_lead_status TEXT;
  v_lead_source TEXT := 'permit_ingest';

  -- JSON metadata capture (if raw_data present)
  v_metadata JSONB := '{}'::jsonb;

  -- Flags for optional columns (queried once)
  has_external_permit_id BOOLEAN := FALSE;
  has_service_column BOOLEAN := FALSE;
  has_trade_column BOOLEAN := FALSE;
  has_metadata_column BOOLEAN := FALSE;
  has_raw_data_column BOOLEAN := FALSE;
  has_applicant_column BOOLEAN := FALSE;
  has_owner_column BOOLEAN := FALSE;
  has_contractor_name_column BOOLEAN := FALSE;
  has_work_class_column BOOLEAN := FALSE;
  has_work_description_column BOOLEAN := FALSE;
  has_description_column BOOLEAN := FALSE;
  has_zipcode_column BOOLEAN := FALSE;
  has_address_column BOOLEAN := FALSE;
  has_city_column BOOLEAN := FALSE;
  has_state_column BOOLEAN := FALSE;
  has_county_column BOOLEAN := FALSE;
  has_value_column BOOLEAN := FALSE;
  has_status_column BOOLEAN := FALSE;
  has_permit_no_column BOOLEAN := FALSE;
  has_source_record_id_column BOOLEAN := FALSE;

BEGIN
  -- Detect optional columns in leads / permits
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='external_permit_id') INTO has_external_permit_id;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='service') INTO has_service_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='trade') INTO has_trade_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='metadata') INTO has_metadata_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='raw_data') INTO has_raw_data_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='applicant') INTO has_applicant_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='owner') INTO has_owner_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='contractor_name') INTO has_contractor_name_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='work_class') INTO has_work_class_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='work_description') INTO has_work_description_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='description') INTO has_description_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='zipcode') INTO has_zipcode_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='address') INTO has_address_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='city') INTO has_city_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='state') INTO has_state_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='county') INTO has_county_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='value') INTO has_value_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='status') INTO has_status_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='permit_no') INTO has_permit_no_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='permits' AND column_name='source_record_id') INTO has_source_record_id_column;

  -- Resolve canonical permit identifier
  v_canonical_permit_id := COALESCE(
      NULLIF(NEW.permit_id, ''),
      CASE WHEN has_permit_no_column THEN NULLIF(NEW.permit_no, '') ELSE NULL END,
      CASE WHEN has_source_record_id_column THEN NULLIF(NEW.source_record_id, '') ELSE NULL END,
      NEW.id::text
    );

  -- raw_data
  IF has_raw_data_column THEN
    v_metadata := COALESCE(NEW.raw_data, '{}'::jsonb);
  END IF;

  -- Name extraction
  v_lead_name := COALESCE(
      CASE WHEN has_applicant_column THEN NULLIF(TRIM(NEW.applicant), '') ELSE NULL END,
      CASE WHEN has_owner_column THEN NULLIF(TRIM(NEW.owner), '') ELSE NULL END,
      CASE WHEN has_contractor_name_column THEN NULLIF(TRIM(NEW.contractor_name), '') ELSE NULL END,
      'Unknown'
    );

  -- Contact extraction
  IF has_raw_data_column THEN
    v_lead_email := COALESCE(v_metadata->>'email', v_metadata->>'applicant_email', v_metadata->>'owner_email');
    v_lead_phone := COALESCE(v_metadata->>'phone', v_metadata->>'applicant_phone', v_metadata->>'owner_phone');
  END IF;

  -- Location & value
  IF has_address_column THEN v_lead_address := NEW.address; END IF;
  IF has_city_column THEN v_lead_city := NEW.city; END IF;
  IF has_state_column THEN v_lead_state := COALESCE(NEW.state, 'TX'); ELSE v_lead_state := 'TX'; END IF;
  IF has_zipcode_column THEN v_lead_zip := NEW.zipcode; END IF;
  IF has_county_column THEN v_lead_county := NEW.county; END IF;
  IF has_value_column THEN v_lead_value := NEW.value; END IF;
  IF has_status_column THEN v_lead_status := NEW.status; END IF;

  -- Service/trade categorization
  DECLARE
    v_text_for_classification TEXT := COALESCE(
        CASE WHEN has_work_description_column THEN NULLIF(NEW.work_description,'') ELSE NULL END,
        CASE WHEN has_description_column THEN NULLIF(NEW.description,'') ELSE NULL END,
        ''
      );
    v_work_class TEXT := CASE WHEN has_work_class_column THEN NEW.work_class ELSE NULL END;
    v_permit_type TEXT := CASE WHEN NEW.permit_type IS NOT NULL THEN NEW.permit_type ELSE NULL END;
  BEGIN
    v_lead_service := CASE
      WHEN v_text_for_classification ILIKE '%hvac%' OR v_text_for_classification ILIKE '%air%' OR v_text_for_classification ILIKE '%heating%' OR v_text_for_classification ILIKE '%cooling%' THEN 'HVAC'
      WHEN v_text_for_classification ILIKE '%electrical%' OR v_text_for_classification ILIKE '%electric%' THEN 'Electrical'
      WHEN v_text_for_classification ILIKE '%plumb%' OR v_text_for_classification ILIKE '%plumbing%' THEN 'Plumbing'
      WHEN v_text_for_classification ILIKE '%roof%' THEN 'Roofing'
      WHEN v_text_for_classification ILIKE '%solar%' THEN 'Solar'
      WHEN v_permit_type ILIKE '%building%' OR v_permit_type ILIKE '%residential%' THEN 'General Construction'
      WHEN v_work_class IS NOT NULL AND v_work_class <> '' THEN v_work_class
      ELSE 'Home Services'
    END;
  END;
  v_lead_trade := v_lead_service;

  -- Duplicate prevention
  IF has_external_permit_id THEN
    IF EXISTS (SELECT 1 FROM public.leads l WHERE l.external_permit_id = v_canonical_permit_id LIMIT 1) THEN
      RETURN NEW;
    END IF;
  ELSE
    IF EXISTS (SELECT 1 FROM public.leads l WHERE l.permit_id = v_permit_uuid LIMIT 1) THEN
      RETURN NEW;
    END IF;
  END IF;

  -- Enrich metadata
  IF has_metadata_column THEN
    v_metadata := v_metadata || jsonb_build_object(
        'canonical_permit_id', v_canonical_permit_id,
        'permit_uuid', v_permit_uuid::text,
        'source', NEW.source,
        'jurisdiction', NEW.jurisdiction,
        'work_class', v_work_class,
        'permit_type', v_permit_type
      );
  END IF;

  -- Insert lead
  IF has_external_permit_id OR has_metadata_column OR has_service_column OR has_trade_column THEN
    INSERT INTO public.leads (
      id, name, permit_id, external_permit_id, service, trade, source, email, phone, value, status, county, created_at, metadata
    )
    SELECT gen_random_uuid(), v_lead_name, v_permit_uuid,
           CASE WHEN has_external_permit_id THEN v_canonical_permit_id ELSE NULL END,
           CASE WHEN has_service_column THEN v_lead_service ELSE NULL END,
           CASE WHEN has_trade_column THEN v_lead_trade ELSE NULL END,
           v_lead_source, v_lead_email, v_lead_phone, v_lead_value, v_lead_status, v_lead_county, NOW(),
           CASE WHEN has_metadata_column THEN v_metadata ELSE NULL END;
  ELSE
    INSERT INTO public.leads (id, name, permit_id, value, status, county, created_at)
    VALUES (gen_random_uuid(), v_lead_name, v_permit_uuid, v_lead_value, v_lead_status, v_lead_county, NOW());
  END IF;

  RETURN NEW;
END;
$$;

-- Trigger creation
CREATE TRIGGER trg_lead_from_permit
AFTER INSERT ON public.permits
FOR EACH ROW
EXECUTE FUNCTION public.create_lead_from_permit();

-- COMMIT;

-- Verification (manual):
-- INSERT INTO public.permits (id, source, source_record_id, permit_no, permit_id, jurisdiction, county, status, address, city, state, zipcode, value, issued_date)
-- VALUES (gen_random_uuid(), 'selftest', 'sent-2', 'SENT-2', 'SENT-2', 'Austin', 'Travis', 'Issued', '200 Test Ave', 'Austin', 'TX', '78701', 55555, now());
-- SELECT id, name, service, trade, external_permit_id, permit_id, source, metadata FROM public.leads ORDER BY created_at DESC LIMIT 1;