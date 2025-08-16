# Supabase Schema Alignment – Permit → Lead Trigger (v2)

Date: August 16, 2025
Migrations Introduced:
- 20250816_add_missing_columns_companion.sql
- 20250816_update_create_lead_from_permit.sql

## Overview

The v2 permit → lead pipeline introduces a resilient trigger-based process that automatically creates enriched lead records whenever a new permit row is inserted. It supports heterogeneous (partially migrated) schemas by dynamically detecting optional columns at runtime.

## Components

| File | Purpose |
|------|---------|
| 20250816_add_missing_columns_companion.sql | Adds / backfills required structural columns and indexes (permits + leads) |
| 20250816_update_create_lead_from_permit.sql | Rebuilds trigger function with canonical ID resolution, enrichment & duplicate prevention |

## Canonical Identifier Resolution

Order of precedence (first non-empty):
1. permits.permit_id
2. permits.permit_no
3. permits.source_record_id
4. permits.id::uuid::text (fallback)

Stored in leads.external_permit_id when that column exists.

## Name Extraction Priority

applicant > owner > contractor_name > 'Unknown'

## Service / Trade Classification

Heuristic pattern matching on (in order):
1. work_description
2. description
3. permit_type
4. work_class
5. fallback: 'Home Services'

Both service and trade set to the resolved value (mirrored if both columns exist).

## Duplicate Prevention

Strategy depends on schema state:

- If leads.external_permit_id exists: skip insert when a lead already has that external_permit_id.
- Else fallback to uniqueness by leads.permit_id (UUID foreign key).

Supporting indexes:
- uq_leads_external_permit_id (partial: WHERE external_permit_id IS NOT NULL)
- uq_leads_permit_uuid (optional 1:1 enforcement)
- uq_permits_source_permit_id (partial: WHERE permit_id IS NOT NULL)

## Metadata Enrichment

If leads.metadata and permits.raw_data exist:

Merged JSON includes:
- canonical_permit_id
- permit_uuid
- source
- jurisdiction
- work_class
- permit_type
(plus original raw_data keys)

## Companion Migration Details

Adds / ensures (if missing):

Permits columns:
permit_id, applicant, owner, contractor_name, work_class, work_description,
raw_data JSONB, provenance JSONB, application_date, finaled_at,
expiration_date, record_hash

Leads columns:
service, trade, external_permit_id, metadata JSONB, source

Backfills:
- permit_id from permit_no / source_record_id
- application_date from applied_date (if present)
- external_permit_id via join (leads.permit_id → permits.id)
- record_hash = md5 concatenation of key attributes
- service/trade synchronized if only one side populated

## Deployment Order

1. Run companion structural migration.
2. Run trigger migration.
3. Run sentinel insert to validate behavior.

## Sentinel Validation Example

```sql
INSERT INTO public.permits (
  id, source, source_record_id, permit_no, permit_id,
  jurisdiction, county, status, address, city, state, zipcode, value, issued_date
) VALUES (
  gen_random_uuid(), 'selftest', 'sent-v2', 'SENT-V2', 'SENT-V2',
  'Austin', 'Travis', 'Issued', '123 Trigger Ln', 'Austin', 'TX', '78701', 42000, now()
);

SELECT id, name, service, trade, external_permit_id, permit_id, source, metadata
FROM public.leads
WHERE external_permit_id = 'SENT-V2'
LIMIT 1;
```

Expected:
- One lead
- service = trade (classified)
- metadata contains canonical_permit_id & permit_uuid

## Idempotency & Safety

The trigger function:
- Drops prior trigger/function only if they exist
- Checks column existence at runtime (information_schema)
- Returns NEW early when duplicate detected

The migrations:
- Use IF NOT EXISTS guards for columns & indexes
- Avoid irreversible destructive operations

## Rollback Outline (Manual)

1. DROP TRIGGER trg_lead_from_permit ON public.permits;
2. DROP FUNCTION public.create_lead_from_permit();
3. (Optional) DROP newly added columns / indexes if reverting schema.
4. Recreate legacy trigger/function if needed.

## Alignment Test Considerations

Automated schema alignment tests should assert:
- Trigger existence & function name: create_lead_from_permit
- Required indexes (uq_permits_source_permit_id, uq_leads_external_permit_id)
- Presence of external_permit_id, metadata in leads (if migration applied)
- Duplicate insert attempt does not increase lead count
- Classification fallback is 'Home Services'

## Extended Duplicate Guard Test

```sql
-- First insert
INSERT INTO public.permits (id, source, permit_id, jurisdiction, county, status, issued_date)
VALUES (gen_random_uuid(), 'dup-test', 'DUP-EX-1', 'Austin', 'Travis', 'Issued', now());

-- Second insert with same canonical ID
INSERT INTO public.permits (id, source, permit_id, jurisdiction, county, status, issued_date)
VALUES (gen_random_uuid(), 'dup-test', 'DUP-EX-1', 'Austin', 'Travis', 'Issued', now());

SELECT COUNT(*) AS lead_count
FROM public.leads
WHERE external_permit_id = 'DUP-EX-1';
```

Expected: lead_count = 1

## Future Enhancements (Tracking Ideas)

- Advanced NLP-based trade classification
- Change-detection (update) trigger using record_hash diff
- Soft-update of leads when permit fields change (status/value)

---
This document accompanies the August 2025 trigger upgrade and should be kept in sync with subsequent migration iterations.