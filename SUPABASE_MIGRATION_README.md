# Supabase Migration for Home Services Lead Generation

This migration creates the necessary database tables and Row Level Security (RLS) policies for the Home Services Lead Generation platform.

## Tables Created

### 1. `public.leads`
- **Note**: This table may already exist in your database
- Stores lead/permit data from various jurisdictions
- Primary key: `id` (BIGSERIAL)

### 2. `public.contractors`
- **New table**: Contractor profiles for authenticated users
- Primary key: `id` (UUID, defaults to `auth.uid()`)
- Fields: email, company_name, phone, trade_specialties, service_areas, license_number, is_verified

### 3. `public.lead_feedback`
- **Note**: This table may already exist in your database
- Stores contractor feedback on leads for ML training
- Links contractors to leads via `account_id` and `lead_id`

### 4. `public.contractor_engagement`
- **New table**: Tracks contractor interactions with leads
- Links contractors to leads with engagement types (viewed, contacted, quoted, won, lost)
- Includes metadata and notes for detailed tracking

## Row Level Security (RLS) Policies

### Leads Table
- **Authenticated INSERT**: Allows authenticated users to insert leads (auth_can_insert policy)
- **Authenticated SELECT**: Allows authenticated users to view all leads (auth_can_select policy)
  - *Note: Anonymous policies have been removed for enhanced security*

### Contractors Table
- **Own Profile Access**: Contractors can SELECT, INSERT, and UPDATE their own profile only
- **Security**: Uses `id = auth.uid()` to ensure users can only access their own data

### Lead Feedback Table
- **Own Feedback Access**: Contractors can INSERT and SELECT their own feedback only
- **Security**: Uses `account_id = auth.uid()` to ensure users can only access their own feedback

### Contractor Engagement Table
- **Own Engagement Access**: Contractors can INSERT, SELECT, and UPDATE their own engagement records only
- **Security**: Uses `contractor_id = auth.uid()` to ensure users can only access their own engagement data

## Installation Instructions

### Option 1: Run in Supabase SQL Editor
1. Copy the contents of `supabase_migration.sql`
2. Paste into your Supabase project's SQL Editor
3. Click "Run" to execute the migration
4. The script includes safety checks and will not fail if tables already exist

### Option 2: Use with Migration System
1. Place `004_supabase_rls_and_missing_tables.sql` in your migrations directory
2. Run your migration system to apply the changes

## Testing the Migration

Use the queries in `supabase_migration_tests.sql` to verify the migration worked correctly:

1. **RLS Verification**: Check that RLS is enabled on all tables
2. **Policy Testing**: Test that users can only access their own data
3. **Anonymous Access**: Verify anonymous users can insert leads (if enabled)

## Important Notes

### Security Considerations
- **Authenticated-Only Access**: All lead operations now require authentication for enhanced security
- **Service Key Backend**: Use service key from your backend for secure server-side operations
- **User Isolation**: All user data is isolated using `auth.uid()` - users cannot access other users' data

### Database Dependencies
- Requires Supabase Auth (`auth.uid()` function)
- Uses standard PostgreSQL features (UUIDs, JSONB, arrays)
- Foreign key constraints ensure data integrity

### Migration Safety
- Uses `IF NOT EXISTS` clauses to prevent conflicts
- Includes `DROP POLICY IF EXISTS` to allow re-running
- Handles missing foreign key constraints gracefully

## Schema Overview

```sql
-- Contractor profile (1 per user)
public.contractors (id = auth.uid())
  ├── Basic info (email, company_name, phone)
  ├── Business details (trade_specialties[], service_areas[])
  └── Verification (license_number, is_verified)

-- Lead data (shared across all users for viewing)
public.leads (id)
  ├── Permit details (jurisdiction, permit_id, address)
  ├── Project info (description, work_class, category)
  └── Enrichment data (location, scoring, etc.)

-- User feedback on leads (private per user)
public.lead_feedback (account_id = auth.uid())
  ├── Rating (no_answer, bad_contact, not_qualified, quoted, won)
  ├── Deal info (deal_band, reason_codes[])
  └── Notes

-- User engagement tracking (private per user)
public.contractor_engagement (contractor_id = auth.uid())
  ├── Engagement type (viewed, contacted, quoted, won, lost)
  ├── Timing (engagement_date, created_at)
  └── Details (notes, metadata)
```

## Troubleshooting

### Common Issues
1. **"relation does not exist"**: Ensure the `leads` table exists before running the migration
2. **"duplicate key value"**: Foreign key constraints may fail if data integrity issues exist
3. **"permission denied"**: Ensure you're running as a database owner/admin

### Authentication Required
All operations on the leads table now require authentication. Ensure your application:
- Uses authenticated Supabase client for lead operations
- Has proper user authentication setup
- Uses service role key for backend operations

### Policy Conflicts
If policies already exist with different names, you may need to drop them manually:
```sql
SELECT policyname FROM pg_policies WHERE tablename = 'leads';
DROP POLICY "old_policy_name" ON public.leads;
```