# Public Leads Table Setup Scripts

This directory contains SQL scripts to manage the `public.leads` table according to the exact requirements specified.

## Files

### 1. `check_leads_table.sql`
Diagnostic script to check if the `public.leads` table exists and has the correct schema.

**Usage:** Run this first to check the current state of your database.

### 2. `create_leads_table.sql`
Creates the `public.leads` table with the exact required schema if it doesn't exist:

**Table Schema:**
- `id` UUID PRIMARY KEY DEFAULT gen_random_uuid()
- `created_at` TIMESTAMPTZ DEFAULT now()
- `name` TEXT
- `email` TEXT
- `phone` TEXT
- `source` TEXT
- `status` TEXT DEFAULT 'new'
- `metadata` JSONB

**Features:**
- Enables Row Level Security (RLS)
- Adds temporary anonymous insert/select policies for testing
- Includes a test record insertion

### 3. `remove_temp_policies.sql`
Removes temporary anonymous policies and replaces them with authenticated-only policies for production use.

**Policies Created:**
- `authenticated_users_insert_leads` - Allows authenticated users to insert
- `authenticated_users_select_leads` - Allows authenticated users to select
- `authenticated_users_update_leads` - Allows authenticated users to update
- `service_role_full_access_leads` - Allows service role full access for backend

## Usage Workflow

1. **Check Current State:**
   ```sql
   -- Run check_leads_table.sql in Supabase SQL Editor
   ```

2. **Create Table (if needed):**
   ```sql
   -- Run create_leads_table.sql in Supabase SQL Editor
   ```

3. **Test Your Application:**
   - Use the temporary anon policies to test lead insertion/selection
   - Verify everything works as expected

4. **Switch to Production Policies:**
   ```sql
   -- Run remove_temp_policies.sql in Supabase SQL Editor
   ```

## Security Notes

⚠️ **Important:** The temporary anonymous policies (`temp_anon_insert_leads` and `temp_anon_select_leads`) allow any unauthenticated user to insert and view all leads. These are **only for testing purposes** and should be removed before production deployment using the `remove_temp_policies.sql` script.

## Testing

After running `create_leads_table.sql`, you can test the setup by:

1. Inserting a lead via anon access (should work)
2. Selecting leads via anon access (should work) 
3. Running your E2E tests
4. After validation, run `remove_temp_policies.sql` to secure the table

## Requirements Met

✅ Creates `public.leads` table with exact specified schema  
✅ Enables RLS on the table  
✅ Adds temporary anon insert/select policies for testing  
✅ Provides script to drop temp policies and switch to authenticated  
✅ All operations are idempotent (safe to run multiple times)