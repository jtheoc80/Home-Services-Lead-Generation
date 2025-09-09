-- ===================================================================
-- GitHub Agent Outbox + Lead Event Triggers
-- ===================================================================
-- Creates event outbox table and lead-specific triggers for GitHub agent integration
-- This enables durable event delivery from lead changes to GitHub

-- Enable pgcrypto extension for gen_random_uuid() function
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ===================================================================
-- 1) Event Outbox Table
-- ===================================================================

CREATE TABLE IF NOT EXISTS public.event_outbox (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type         TEXT NOT NULL,              -- e.g. 'lead.created', 'lead.status_changed'
    payload      JSONB NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ
);

-- Indexes for efficient queries
CREATE INDEX IF NOT EXISTS event_outbox_created_idx ON public.event_outbox (created_at);
CREATE INDEX IF NOT EXISTS event_outbox_pending_idx ON public.event_outbox (delivered_at NULLS FIRST);
CREATE INDEX IF NOT EXISTS event_outbox_type_idx ON public.event_outbox (type);

-- ===================================================================
-- 2) Lead Created Event Trigger Function
-- ===================================================================

CREATE OR REPLACE FUNCTION public.emit_lead_created_to_outbox()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Mirror the public_leads view filters - only emit events for leads that would be visible
    -- public_leads view selects: id, source, external_permit_id, trade, address, zip->zipcode, county->jurisdiction, status, created_at, updated_at
    -- No specific filters applied in the view, so all leads are eligible
    
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
            'trade', NEW.trade,
            'address', NEW.address,
            'city', NEW.city,
            'state', NEW.state,
            'zip', NEW.zip,
            'county', NEW.county,
            'service', NEW.service,
            'value', NEW.value,
            'lead_score', NEW.lead_score,
            'score_label', NEW.score_label,
            'permit_id', NEW.permit_id,
            'external_permit_id', NEW.external_permit_id,
            'metadata', NEW.metadata,
            'created_at', NEW.created_at,
            'updated_at', NEW.updated_at
        )
    );
    RETURN NEW;
END;
$$;

-- ===================================================================
-- 3) Lead Status Changed Event Trigger Function
-- ===================================================================

CREATE OR REPLACE FUNCTION public.emit_lead_status_changed_to_outbox()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    -- Only emit if status actually changed
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        -- Mirror the public_leads view filters - only emit events for leads that would be visible
        -- public_leads view selects: id, source, external_permit_id, trade, address, zip->zipcode, county->jurisdiction, status, created_at, updated_at
        -- No specific filters applied in the view, so all leads are eligible
        
        INSERT INTO public.event_outbox(type, payload)
        VALUES (
            'lead.status_changed',
            jsonb_build_object(
                'id', NEW.id,
                'name', NEW.name,
                'email', NEW.email,
                'phone', NEW.phone,
                'source', NEW.source,
                'old_status', OLD.status,
                'new_status', NEW.status,
                'trade', NEW.trade,
                'address', NEW.address,
                'city', NEW.city,
                'state', NEW.state,
                'zip', NEW.zip,
                'county', NEW.county,
                'service', NEW.service,
                'value', NEW.value,
                'lead_score', NEW.lead_score,
                'score_label', NEW.score_label,
                'permit_id', NEW.permit_id,
                'external_permit_id', NEW.external_permit_id,
                'metadata', NEW.metadata,
                'created_at', NEW.created_at,
                'updated_at', NEW.updated_at
            )
        );
    END IF;
    RETURN NEW;
END;
$$;

-- ===================================================================
-- 4) Create Triggers on public.leads Table
-- ===================================================================

-- Check if status column exists before creating UPDATE trigger
DO $$
BEGIN
    -- Lead creation trigger (always create)
    DROP TRIGGER IF EXISTS trg_emit_lead_created_to_outbox ON public.leads;
    CREATE TRIGGER trg_emit_lead_created_to_outbox
        AFTER INSERT ON public.leads
        FOR EACH ROW
        EXECUTE FUNCTION public.emit_lead_created_to_outbox();

    -- Lead status change trigger (only if status column exists)
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'leads' 
        AND column_name = 'status'
    ) THEN
        DROP TRIGGER IF EXISTS trg_emit_lead_status_changed_to_outbox ON public.leads;
        CREATE TRIGGER trg_emit_lead_status_changed_to_outbox
            AFTER UPDATE OF status ON public.leads
            FOR EACH ROW
            EXECUTE FUNCTION public.emit_lead_status_changed_to_outbox();
    END IF;
END $$;

-- ===================================================================
-- 5) Helper Functions for Event Management
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

-- ===================================================================
-- 6) Documentation
-- ===================================================================

COMMENT ON TABLE public.event_outbox IS 'Event outbox for GitHub agent integration - stores events for durable delivery';
COMMENT ON FUNCTION public.emit_lead_created_to_outbox() IS 'Trigger function to emit lead.created events to outbox when new leads are inserted';
COMMENT ON FUNCTION public.emit_lead_status_changed_to_outbox() IS 'Trigger function to emit lead.status_changed events to outbox when lead status is updated';

-- Verification message
SELECT 'GitHub agent outbox + lead triggers setup complete! Event outbox table, lead triggers, and helper functions created.' AS message;