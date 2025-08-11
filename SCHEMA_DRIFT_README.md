# Schema Drift Detection

This repository includes an automated schema drift detection system that compares the local `backend/app/models.sql` file with the live Supabase database schema.

## Overview

The schema drift detection system:
- 🔍 Compares local `models.sql` with live Supabase schema
- 📝 Generates migration SQL when differences are found
- 🤖 Automatically creates pull requests for manual review
- ⚡ Runs daily via GitHub Actions (and on model changes)

## Components

### 1. Schema Drift Checker Script
**File:** `scripts/schema-drift-check.ts`

A TypeScript script that:
- Parses the local `backend/app/models.sql` file
- Connects to Supabase using the service role (read-only)
- Extracts live schema information
- Compares schemas and identifies differences
- Generates migration SQL and detailed comparison reports

### 2. GitHub Workflow
**File:** `.github/workflows/schema-drift.yml`

Automated workflow that:
- Runs daily at 2 AM UTC
- Triggers on changes to `models.sql`
- Can be manually triggered
- Creates PRs when drift is detected
- Includes comprehensive error handling

### 3. Supabase Schema Functions (Optional)
**File:** `scripts/supabase-schema-functions.sql`

Optional PostgreSQL functions that can be installed in Supabase to enable more detailed schema introspection:
- `get_table_schema_info()` - Extract table and column information
- `get_index_info()` - Extract index information

## Setup

### Prerequisites
- Supabase project with service role key
- GitHub repository secrets configured:
  - `NEXT_PUBLIC_SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`

### Installation

1. **Files are already included** in this repository:
   - Workflow: `.github/workflows/schema-drift.yml`
   - Script: `scripts/schema-drift-check.ts`
   - Functions: `scripts/supabase-schema-functions.sql`

2. **Optional: Install Supabase functions** (recommended for better schema detection):
   ```sql
   -- Run this in your Supabase SQL editor
   \i scripts/supabase-schema-functions.sql
   ```

3. **Verify secrets** are configured in GitHub:
   - Go to Settings → Secrets and variables → Actions
   - Ensure `SUPABASE_SERVICE_ROLE_KEY` is set
   - Ensure `NEXT_PUBLIC_SUPABASE_URL` is set

## Usage

### Manual Execution
```bash
# Run schema drift check locally
npm run schema:drift

# Or using npx
npx tsx scripts/schema-drift-check.ts
```

### Automatic Execution
The workflow runs automatically:
- **Daily** at 2 AM UTC
- **On push** to main branch when `models.sql` changes
- **Manual trigger** via GitHub Actions UI

## Output Files

When drift is detected, the script generates:

1. **`schema-drift-migration.sql`** - Generated migration SQL
2. **`schema-drift-details.json`** - Detailed comparison results

These files are automatically included in the PR created by the workflow.

## Exit Codes

- `0` - No drift detected
- `1` - Drift detected (triggers PR creation)  
- `2` - Error occurred

## Schema Detection Methods

The script uses multiple fallback methods for schema detection:

1. **Custom Functions** (preferred) - Uses PostgreSQL functions if installed
2. **Direct Access** - Attempts to access system views directly
3. **Table Discovery** - Tests table existence by querying known tables

## Limitations

- Column-level details may be limited depending on Supabase configuration
- Index and constraint detection requires custom functions
- Some schema differences may require manual review
- The script uses read-only access and cannot automatically apply migrations

## Troubleshooting

### Common Issues

1. **Service role permissions**
   - Ensure service role key has read access to tables
   - Check that RLS policies allow service role access

2. **Missing schema information**
   - Install optional Supabase functions for better detection
   - Check Supabase logs for permission errors

3. **Workflow failures**
   - Verify GitHub secrets are correctly configured
   - Check workflow logs for detailed error messages

### Manual Testing

Test the connection and permissions:
```bash
# Test Supabase connection
npm run supa:smoke

# Test schema drift detection
npm run schema:drift
```

## Integration with Development Workflow

1. **Make schema changes** in `backend/app/models.sql`
2. **Apply changes** to your development database
3. **Push changes** - workflow automatically detects differences
4. **Review PR** created by the workflow
5. **Apply migration** after review and testing
6. **Update models.sql** if needed to reflect final state

## Contributing

When modifying the schema drift detection:

1. Test changes locally with `npm run schema:drift`
2. Ensure TypeScript compilation with `npx tsc --noEmit scripts/schema-drift-check.ts`
3. Update this README if adding new features
4. Test with both real and mock Supabase connections

## Security Notes

- Uses service role key for read-only schema access
- No write operations are performed automatically
- All migrations require manual review and approval
- Sensitive data is not included in generated reports