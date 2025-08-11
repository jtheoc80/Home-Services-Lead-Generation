# Leads Table Setup Script

This PostgreSQL script creates the `public.leads` table for Supabase with the exact specifications required for the Home Services Lead Generation platform.

## Features

- ✅ Creates `pgcrypto` extension for UUID generation
- ✅ Creates `public.leads` table with UUID primary key
- ✅ Enables Row Level Security (RLS)
- ✅ Adds temporary policies for anonymous access
- ✅ Inserts seed data for testing

## Table Schema

```sql
public.leads (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz default now(),
    name text,
    email text,
    phone text,
    source text,
    status text default 'new',
    metadata jsonb
)
```

## Security Policies

### Anonymous Role Policies (TEMPORARY)
- **Insert Policy**: Allows anonymous users to insert new leads
- **Select Policy**: Allows anonymous users to select all leads

> **Warning**: These are temporary policies for development/testing. Remove or modify for production use.

## Seed Data

The script inserts one test record:
```sql
name='Smoke Test', email='smoke@example.com', source='manual'
```

## Usage

### In Supabase SQL Editor
1. Open your Supabase project's SQL Editor
2. Copy the contents of `leads_table_setup.sql`
3. Paste and execute the script

### Command Line (if you have direct PostgreSQL access)
```bash
psql -h your-host -d your-database -f docs/supabase/leads_table_setup.sql
```

## Script Safety

- Uses `create extension if not exists` to avoid conflicts
- Uses `create table if not exists` to prevent errors if table exists
- Uses `drop policy if exists` before creating policies
- Uses `on conflict do nothing` for seed data insertion

## Verification

After running the script, you can verify the setup with:

```sql
-- Check table exists with correct columns
\d public.leads

-- Check RLS is enabled
SELECT schemaname, tablename, rowsecurity 
FROM pg_tables 
WHERE tablename = 'leads';

-- Check policies exist
SELECT policyname, roles, cmd, qual 
FROM pg_policies 
WHERE tablename = 'leads';

-- Check seed data
SELECT * FROM public.leads WHERE name = 'Smoke Test';
```

## Notes

- This script creates a standalone leads table that may differ from other tables in the project
- The anonymous access policies are marked as "TEMP" and should be reviewed for production use
- The `metadata` column uses JSONB for flexible data storage
- UUID primary keys provide better distribution and security than sequential integers