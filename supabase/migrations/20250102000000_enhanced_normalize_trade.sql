-- Enhanced permit→lead trigger with normalize_trade logic integration
-- This migration enhances the create_lead_from_permit() function with better trade derivation
-- that follows the same logic as the Python normalize_trade function

-- ====== STEP 1: CREATE ENHANCED normalize_trade_from_permit FUNCTION ======
CREATE OR REPLACE FUNCTION public.normalize_trade_from_permit(
    work_description TEXT,
    permit_type TEXT,
    permit_class TEXT
) RETURNS TEXT 
LANGUAGE plpgsql
AS $$
DECLARE
    combined_text TEXT;
    trade_result TEXT;
BEGIN
    -- Combine all text for analysis (similar to Python function)
    combined_text := LOWER(COALESCE(work_description, '') || ' ' || COALESCE(permit_type, '') || ' ' || COALESCE(permit_class, ''));
    
    -- Priority-based trade detection (highest priority wins)
    -- Check for high-value specialty trades first
    IF combined_text ~ '.*(roof|roofing|shingle|gutter|eave).*' THEN
        trade_result := 'Roofing';
    ELSIF combined_text ~ '.*(solar|photovoltaic|pv|renewable).*' THEN
        trade_result := 'Solar';
    ELSIF combined_text ~ '.*(pool|spa|jacuzzi|hot tub|swimming).*' THEN
        trade_result := 'Pool';
    ELSIF combined_text ~ '.*(kitchen|cabinet|countertop|appliance).*' THEN
        trade_result := 'Kitchen';
    ELSIF combined_text ~ '.*(bath|bathroom|shower|toilet|vanity|tub).*' THEN
        trade_result := 'Bath';
    ELSIF combined_text ~ '.*(hvac|heating|cooling|air condition|furnace|heat pump).*' THEN
        trade_result := 'HVAC';
    ELSIF combined_text ~ '.*(electrical|electric|wiring|panel|outlet).*' THEN
        trade_result := 'Electrical';
    ELSIF combined_text ~ '.*(plumb|water|sewer|pipe|drain).*' THEN
        trade_result := 'Plumbing';
    ELSIF combined_text ~ '.*(foundation|slab|footing|pier|basement).*' THEN
        trade_result := 'Foundation';
    ELSIF combined_text ~ '.*(window|glazing|glass|sash).*' THEN
        trade_result := 'Windows';
    ELSIF combined_text ~ '.*(fence|fencing|gate|barrier).*' THEN
        trade_result := 'Fence';
    ELSE
        trade_result := NULL;
    END IF;
    
    -- If no keyword matches, fallback to permit_type analysis
    IF trade_result IS NULL THEN
        IF permit_type IS NOT NULL AND permit_type != '' AND permit_type != 'null' THEN
            IF LOWER(permit_type) ~ '.*(residential|building|house).*' THEN
                trade_result := 'General Construction';
            ELSIF LOWER(permit_type) ~ '.*(commercial|office).*' THEN
                trade_result := 'Commercial';
            ELSIF LOWER(permit_type) ~ '.*(electrical|electric).*' THEN
                trade_result := 'Electrical';
            ELSIF LOWER(permit_type) ~ '.*(plumbing|plumb).*' THEN
                trade_result := 'Plumbing';
            ELSIF LOWER(permit_type) ~ '.*(mechanical|hvac).*' THEN
                trade_result := 'HVAC';
            ELSE
                trade_result := INITCAP(permit_type);
            END IF;
        END IF;
    END IF;
    
    -- If still no match, try permit_class
    IF trade_result IS NULL THEN
        IF permit_class IS NOT NULL AND permit_class != '' AND permit_class != 'null' THEN
            trade_result := INITCAP(permit_class);
        END IF;
    END IF;
    
    -- Final fallback
    RETURN COALESCE(trade_result, 'General');
END;
$$;

-- ====== STEP 2: UPDATE create_lead_from_permit() FUNCTION ======
CREATE OR REPLACE FUNCTION public.create_lead_from_permit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  v_name text;
  v_trade text;
BEGIN
  -- Build name from available fields
  v_name := COALESCE(
    NULLIF(NEW.work_description,''),
    'Permit ' || COALESCE(NEW.permit_number, NEW.permit_id, NEW.id::text, '(no #)')
  );
  
  -- Use enhanced normalize_trade_from_permit function
  v_trade := normalize_trade_from_permit(
    NEW.work_description,
    NEW.permit_type, 
    NEW.permit_class
  );

  INSERT INTO public.leads (permit_id, name, trade, county, status, value, lead_score, created_at)
  VALUES (
    NEW.id, 
    v_name, 
    v_trade, 
    NULLIF(NEW.county,''), 
    COALESCE(NULLIF(NEW.status,''),'New'),
    NEW.valuation, 
    75, 
    COALESCE(NEW.issued_date, NOW())
  )
  ON CONFLICT (permit_id) DO NOTHING;

  RETURN NEW;
END;
$$;

-- ====== STEP 3: ADD COMMENTS ======
COMMENT ON FUNCTION public.normalize_trade_from_permit(TEXT, TEXT, TEXT) IS 'Enhanced trade normalization function that uses keyword priority and sophisticated fallback logic matching the Python normalize_trade function';
COMMENT ON FUNCTION public.create_lead_from_permit() IS 'Enhanced trigger function that creates leads from permits using sophisticated trade derivation with keyword priority and fallback logic';

-- Success message
SELECT 'Enhanced permit→lead trigger deployed with sophisticated trade normalization!' AS message;