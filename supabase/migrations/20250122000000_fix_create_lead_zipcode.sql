-- Update create_lead_from_permit function to include zip field in INSERT statements
-- This migration fixes the missing zip field in the lead creation trigger

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
  has_zip_column_in_leads BOOLEAN := FALSE;

BEGIN
  -- Detect optional columns in leads / permits
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='external_permit_id') INTO has_external_permit_id;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='service') INTO has_service_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='trade') INTO has_trade_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='metadata') INTO has_metadata_column;
  SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='leads' AND column_name='zip') INTO has_zip_column_in_leads;
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
    CASE WHEN has_permit_no_column AND NEW.permit_no IS NOT NULL AND NEW.permit_no != '' THEN NEW.permit_no ELSE NULL END,
    NEW.permit_id,
    CASE WHEN has_source_record_id_column AND NEW.source_record_id IS NOT NULL AND NEW.source_record_id != '' THEN NEW.source_record_id ELSE NULL END,
    NEW.id::TEXT
  );

  -- Extract lead name (prefer applicant → owner → contractor → default)
  v_lead_name := COALESCE(
    CASE WHEN has_applicant_column THEN NULLIF(trim(NEW.applicant), '') ELSE NULL END,
    CASE WHEN has_owner_column THEN NULLIF(trim(NEW.owner), '') ELSE NULL END,
    CASE WHEN has_contractor_name_column THEN NULLIF(trim(NEW.contractor_name), '') ELSE NULL END,
    'Unknown'
  );

  -- Extract contact info from raw_data if available
  IF has_raw_data_column AND NEW.raw_data IS NOT NULL THEN
    v_lead_email := COALESCE(
      NEW.raw_data->>'email',
      NEW.raw_data->>'applicant_email',
      NEW.raw_data->>'owner_email'
    );
    v_lead_phone := COALESCE(
      NEW.raw_data->>'phone',
      NEW.raw_data->>'applicant_phone',
      NEW.raw_data->>'owner_phone'
    );
    v_metadata := NEW.raw_data;
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
    v_permit_type TEXT := COALESCE(NEW.permit_type, '');
    v_work_class TEXT := CASE WHEN has_work_class_column THEN COALESCE(NEW.work_class, '') ELSE '' END;
  BEGIN
    -- Determine service category
    v_lead_service := CASE 
      WHEN v_text_for_classification ILIKE '%hvac%' OR v_text_for_classification ILIKE '%air%' OR v_text_for_classification ILIKE '%heating%' OR v_text_for_classification ILIKE '%cooling%' THEN 'HVAC'
      WHEN v_text_for_classification ILIKE '%electrical%' OR v_text_for_classification ILIKE '%electric%' THEN 'Electrical'
      WHEN v_text_for_classification ILIKE '%plumbing%' OR v_text_for_classification ILIKE '%plumb%' THEN 'Plumbing'
      WHEN v_text_for_classification ILIKE '%roof%' THEN 'Roofing'
      WHEN v_text_for_classification ILIKE '%solar%' THEN 'Solar'
      WHEN v_permit_type ILIKE '%building%' OR v_permit_type ILIKE '%residential%' THEN 'General Construction'
      ELSE 'Home Services'
    END;

    -- Trade is derived from permit_type or work_class
    v_lead_trade := COALESCE(NULLIF(v_permit_type, ''), NULLIF(v_work_class, ''));
  END;

  -- Insert lead with improved column handling
  IF has_service_column OR has_trade_column OR has_metadata_column OR has_external_permit_id OR has_zip_column_in_leads THEN
    INSERT INTO public.leads (
      id, name, permit_id, 
      external_permit_id, 
      service, 
      trade, 
      source, email, phone, 
      address, city, state, zip, county,
      value, status, created_at, 
      metadata
    )
    SELECT gen_random_uuid(), v_lead_name, v_permit_uuid,
           CASE WHEN has_external_permit_id THEN v_canonical_permit_id ELSE NULL END,
           CASE WHEN has_service_column THEN v_lead_service ELSE NULL END,
           CASE WHEN has_trade_column THEN v_lead_trade ELSE NULL END,
           v_lead_source, v_lead_email, v_lead_phone,
           v_lead_address, v_lead_city, v_lead_state,
           CASE WHEN has_zip_column_in_leads THEN v_lead_zip ELSE NULL END,
           v_lead_county, v_lead_value, v_lead_status, NOW(),
           CASE WHEN has_metadata_column THEN v_metadata ELSE NULL END;
  ELSE
    INSERT INTO public.leads (id, name, permit_id, value, status, county, created_at)
    VALUES (gen_random_uuid(), v_lead_name, v_permit_uuid, v_lead_value, v_lead_status, v_lead_county, NOW());
  END IF;

  RETURN NEW;
END;
$$;

COMMENT ON FUNCTION public.create_lead_from_permit() IS 
'Trigger function that creates a lead record from an inserted permit. Maps permits.zipcode to leads.zip field. Handles optional columns gracefully and provides intelligent service categorization.';