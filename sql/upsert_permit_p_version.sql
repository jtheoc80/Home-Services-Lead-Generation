-- Add a version of upsert_permit that accepts parameter 'p' for compatibility
-- with the new API structure while still using the existing permits table

CREATE OR REPLACE FUNCTION public.upsert_permit(p JSONB)
RETURNS TABLE(id UUID, action TEXT) AS $$
DECLARE
  permit_id UUID;
  permit_action TEXT;
  source_val TEXT;
  source_record_id_val TEXT;
BEGIN
  -- Extract required fields from parameter 'p'
  source_val := p->>'source';
  source_record_id_val := p->>'source_record_id';
  
  -- Validate required fields
  IF source_val IS NULL OR source_record_id_val IS NULL THEN
    RAISE EXCEPTION 'source and source_record_id are required fields';
  END IF;

  -- Attempt to update existing record
  UPDATE public.permits SET
    permit_number = p->>'permit_number',
    issued_date = CASE 
      WHEN p->>'issued_date' IS NOT NULL 
      THEN (p->>'issued_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    application_date = CASE 
      WHEN p->>'application_date' IS NOT NULL 
      THEN (p->>'application_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    expiration_date = CASE 
      WHEN p->>'expiration_date' IS NOT NULL 
      THEN (p->>'expiration_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    permit_type = p->>'permit_type',
    permit_class = p->>'permit_class',
    work_description = p->>'work_description',
    address = p->>'address',
    city = p->>'city',
    county = p->>'county',
    zipcode = p->>'zipcode',
    latitude = CASE 
      WHEN p->>'latitude' IS NOT NULL 
      THEN (p->>'latitude')::NUMERIC 
      ELSE NULL 
    END,
    longitude = CASE 
      WHEN p->>'longitude' IS NOT NULL 
      THEN (p->>'longitude')::NUMERIC 
      ELSE NULL 
    END,
    valuation = CASE 
      WHEN p->>'valuation' IS NOT NULL 
      THEN (p->>'valuation')::NUMERIC 
      ELSE NULL 
    END,
    square_feet = CASE 
      WHEN p->>'square_feet' IS NOT NULL 
      THEN (p->>'square_feet')::NUMERIC 
      ELSE NULL 
    END,
    applicant_name = p->>'applicant_name',
    contractor_name = p->>'contractor_name',
    owner_name = p->>'owner_name',
    status = p->>'status',
    raw_data = p,
    updated_at = NOW()
  WHERE source = source_val AND source_record_id = source_record_id_val
  RETURNING public.permits.id INTO permit_id;
  
  -- If update affected a row, return it
  IF permit_id IS NOT NULL THEN
    permit_action := 'updated';
    RETURN QUERY SELECT permit_id, permit_action;
    RETURN;
  END IF;
  
  -- Otherwise, insert new record
  INSERT INTO public.permits (
    source,
    source_record_id,
    permit_number,
    issued_date,
    application_date,
    expiration_date,
    permit_type,
    permit_class,
    work_description,
    address,
    city,
    county,
    zipcode,
    latitude,
    longitude,
    valuation,
    square_feet,
    applicant_name,
    contractor_name,
    owner_name,
    status,
    raw_data
  ) VALUES (
    source_val,
    source_record_id_val,
    p->>'permit_number',
    CASE 
      WHEN p->>'issued_date' IS NOT NULL 
      THEN (p->>'issued_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'application_date' IS NOT NULL 
      THEN (p->>'application_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'expiration_date' IS NOT NULL 
      THEN (p->>'expiration_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    p->>'permit_type',
    p->>'permit_class',
    p->>'work_description',
    p->>'address',
    p->>'city',
    p->>'county',
    p->>'zipcode',
    CASE 
      WHEN p->>'latitude' IS NOT NULL 
      THEN (p->>'latitude')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'longitude' IS NOT NULL 
      THEN (p->>'longitude')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'valuation' IS NOT NULL 
      THEN (p->>'valuation')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'square_feet' IS NOT NULL 
      THEN (p->>'square_feet')::NUMERIC 
      ELSE NULL 
    END,
    p->>'applicant_name',
    p->>'contractor_name',
    p->>'owner_name',
    p->>'status',
    p
  )
  RETURNING public.permits.id INTO permit_id;
  
  permit_action := 'inserted';
  RETURN QUERY SELECT permit_id, permit_action;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION public.upsert_permit(JSONB) IS 'Idempotent upsert function for permit records using parameter p for compatibility with new API structure';

-- Success message
SELECT 'upsert_permit function with parameter p created successfully!' AS message;