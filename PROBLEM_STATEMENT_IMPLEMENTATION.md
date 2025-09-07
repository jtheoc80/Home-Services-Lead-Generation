# Problem Statement Implementation

This document explains how the repository now implements the workflow step specified in the problem statement.

## Problem Statement Requirements

The problem statement required implementation of this workflow step:

```yaml
- name: Create 50 leads from recent permits
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  run: |
    curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":50,"p_days":365}'
```

## Implementation Summary

✅ **Complete Implementation** - The exact workflow step is now available in the repository.

### Files Added/Modified

1. **`.github/workflows/create-leads-sample.yml`** - New workflow that implements the exact step
2. **`validate_function_implementation.py`** - Validation script for testing
3. **`test_problem_statement_implementation.sh`** - Demonstration script

### Key Features

- **Exact Step Implementation**: The workflow contains a step named "Create 50 leads from recent permits"
- **Exact Command**: Uses the precise curl command with `{"p_limit":50,"p_days":365}`
- **Manual Trigger**: Can be run on-demand via GitHub Actions workflow_dispatch
- **Configurable**: Allows customization of limit and days parameters
- **Error Handling**: Includes preflight checks and proper error messages

## How to Use

### 1. Run the Workflow

Navigate to GitHub Actions → "Create 50 Leads Sample" workflow → "Run workflow"

### 2. Test Locally

If you have the required environment variables set:

```bash
# Test the exact implementation
./test_problem_statement_implementation.sh

# Or validate the function
python3 validate_function_implementation.py
```

### 3. Integrate into Other Workflows

The step can be copied to any other workflow:

```yaml
- name: Create 50 leads from recent permits
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  run: |
    curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":50,"p_days":365}'
```

## Technical Details

### Backend Function

The implementation leverages the existing `upsert_leads_from_permits_limit` function:

- **Location**: `supabase/migrations/20250121000000_add_upsert_leads_from_permits_limit.sql`
- **Parameters**: 
  - `p_limit`: Maximum number of leads to create (50 in problem statement)
  - `p_days`: Days back to look for permits (365 in problem statement)
- **Returns**: Object with `inserted_count`, `updated_count`, and `total_processed`

### Function Features

1. **Limit Control**: Processes exactly up to 50 permits (or specified limit)
2. **Date Filtering**: Looks at permits from last 365 days (or specified days)
3. **Conflict Handling**: Updates existing leads if they already exist
4. **Correct Column Usage**: Uses `issued_date` (not `issue_date`) for accurate date filtering
5. **Lead Quality**: Creates comprehensive lead records with proper field mapping

### Testing

The implementation includes comprehensive tests:

- **`test_upsert_leads_from_permits_limit.sql`**: Database function tests
- **`verify_upsert_leads_limit_function.sql`**: Verification queries  
- **Problem statement specific test**: Tests exact parameters `p_limit=50, p_days=365`

## Validation

Run these commands to validate the implementation:

```bash
# 1. Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/create-leads-sample.yml'))"

# 2. Test function availability (requires env vars)
python3 validate_function_implementation.py

# 3. Demonstrate exact implementation (requires env vars) 
./test_problem_statement_implementation.sh
```

## Integration Options

The workflow step can be integrated into existing workflows in several ways:

1. **Add to existing workflows**: Copy the step to `ingest-tx.yml`, `permits-harris.yml`, or `etl.yml`
2. **Use as standalone**: Keep as separate workflow for on-demand lead generation
3. **Customize parameters**: Modify `p_limit` and `p_days` for different use cases
4. **Schedule**: Add cron schedule for automatic execution

## Conclusion

✅ The problem statement requirements are fully implemented and ready for use. The exact workflow step with the specified curl command is available and functional.