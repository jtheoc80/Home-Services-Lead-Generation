-- Fix permit→lead trigger to be robust when permit_type is missing
-- This addresses the issue where NULL values could be inserted into leads.trade
-- when both permit_type and permit_class are empty/null

-- ====== STEP 1: ADD DEFAULT CONSTRAINT TO LEADS.TRADE ======
ALTER TABLE public.leads ALTER COLUMN trade SET DEFAULT 'General';

-- ====== STEP 2: BACKFILL EXISTING NULL VALUES ======
UPDATE public.leads 
SET trade = 'General' 
WHERE trade IS NULL;

-- ====== STEP 3: UPDATE create_lead_from_permit() FUNCTION ======
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
  
  -- Build trade from available fields with robust fallback to 'General'
  -- Uses permit_type first, then permit_class, then defaults to 'General'
  v_trade := COALESCE(
    NULLIF(NEW.permit_type,''), 
    NULLIF(NEW.permit_class,''), 
    'General'
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

-- ====== STEP 4: RECREATE TRIGGER ======
DROP TRIGGER IF EXISTS trg_lead_from_permit ON public.permits;
CREATE TRIGGER trg_lead_from_permit
  AFTER INSERT ON public.permits
  FOR EACH ROW 
  EXECUTE FUNCTION public.create_lead_from_permit();

-- ====== STEP 5: UPDATE EXISTING BACKFILL QUERY ======
-- This ensures any future manual backfills also use the robust logic
COMMENT ON FUNCTION public.create_lead_from_permit() IS 'Enhanced trigger function that creates leads from permits with robust trade derivation: permit_type → permit_class → General fallback';

-- Success message
SELECT 'Permit→lead trigger updated with robust trade derivation. No more NULL trades!' AS message;