-- ===================================================================
-- GitHub Agent Outbox Setup
-- ===================================================================
-- Creates event outbox table and triggers for GitHub agent integration
-- This enables durable event delivery from DB changes to GitHub

-- Enable pgcrypto extension for gen_random_uuid() function
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ===================================================================
-- 1) Event Outbox Table
-- ===================================================================

CREATE TABLE IF NOT EXISTS public.event_outbox (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type         TEXT NOT NULL,              -- e.g. 'permit.created', 'lead.created'
    payload      JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS event_outbox_created_idx ON public.event_outbox (created_at);
CREATE INDEX IF NOT EXISTS event_outbox_pending_idx ON public.event_outbox (delivered_at NULLS FIRST);
CREATE INDEX IF NOT EXISTS event_outbox_type_idx ON public.event_outbox (type);

-- ===================================================================
-- 2) Permit Event Trigger Function
-- ===================================================================

CREATE OR REPLACE FUNCTION public.enqueue_permit_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.event_outbox(type, payload)
    VALUES (
        'permit.created',
        jsonb_build_object(
            'permit_id', NEW.permit_id,
            'id', NEW.id,
            'source_id', NEW.source_id,
            'issued_at', NEW.issued_at,
            'address', NEW.address,
            'city', NEW.city,
            'county', NEW.county,
            'permit_type', NEW.permit_type,
            'permit_class', NEW.permit_class,
            'status', NEW.status,
            'applicant_name', NEW.applicant_name,
            'contractor_name', NEW.contractor_name,
            'owner_name', NEW.owner_name,
            'valuation', NEW.valuation,
            'description', NEW.description,
            'created_at', NEW.created_at
        )
    );
    RETURN NEW;
END;
$$;

-- ===================================================================
-- 3) Lead Event Trigger Function
-- ===================================================================

CREATE OR REPLACE FUNCTION public.enqueue_lead_event()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.event_outbox(type, payload)
    VALUES (
        'lead.created',
        jsonb_build_object(
            'id', NEW.id,
            'name', NEW.name,
            'email', NEW.email,
            'phone', NEW.phone,
            'source', NEW.source,
            'status', NEW.status,
            'metadata', NEW.metadata,
            'created_at', NEW.created_at
        )
    );
    RETURN NEW;
END;
$$;

-- ===================================================================
-- 4) Create Triggers
-- ===================================================================

-- Permit trigger (for gold.permits table)
DROP TRIGGER IF EXISTS trg_enqueue_permit ON gold.permits;
CREATE TRIGGER trg_enqueue_permit
    AFTER INSERT ON gold.permits
    FOR EACH ROW
    EXECUTE FUNCTION public.enqueue_permit_event();

-- Lead trigger (for public.leads table)
DROP TRIGGER IF EXISTS trg_enqueue_lead ON public.leads;
CREATE TRIGGER trg_enqueue_lead
    AFTER INSERT ON public.leads
    FOR EACH ROW
    EXECUTE FUNCTION public.enqueue_lead_event();

-- ===================================================================
-- 5) Test Data and Verification
-- ===================================================================

-- Function to get pending events count
CREATE OR REPLACE FUNCTION public.get_pending_events_count()
RETURNS INTEGER
LANGUAGE SQL
AS $$
    SELECT COUNT(*)::INTEGER FROM public.event_outbox WHERE delivered_at IS NULL;
$$;

-- Function to mark events as delivered (for the agent to use)
CREATE OR REPLACE FUNCTION public.mark_events_delivered(event_ids UUID[])
RETURNS INTEGER
LANGUAGE SQL
AS $$
    UPDATE public.event_outbox 
    SET delivered_at = NOW() 
    WHERE id = ANY(event_ids) AND delivered_at IS NULL;
    
    SELECT COUNT(*)::INTEGER FROM public.event_outbox 
    WHERE id = ANY(event_ids) AND delivered_at IS NOT NULL;
$$;

-- Verification message
SELECT 'GitHub agent outbox setup complete! Tables, triggers, and helper functions created.' AS message;