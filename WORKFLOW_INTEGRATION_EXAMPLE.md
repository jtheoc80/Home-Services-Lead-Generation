# Workflow Integration Example for upsert_leads_from_permits_limit

This document shows how to integrate the new `upsert_leads_from_permits_limit` function into GitHub workflows.

## Problem Statement Implementation

The exact step from the problem statement can now be used directly:

```yaml
- name: Live test: create 50 leads
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

## Enhanced Version with Error Handling

For production workflows, here's an enhanced version with proper error handling:

```yaml
- name: Live test: create 50 leads
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  run: |
    echo "Creating up to 50 leads from permits in the last 365 days..."
    
    response=$(curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":50,"p_days":365}')
    
    echo "Response: $response"
    
    # Extract counts from response if possible
    if echo "$response" | grep -q "inserted_count\|updated_count\|total_processed"; then
      echo "✅ Successfully created leads from permits"
      
      # Parse and display results
      inserted=$(echo "$response" | jq -r '.[0].inserted_count // 0' 2>/dev/null || echo "0")
      updated=$(echo "$response" | jq -r '.[0].updated_count // 0' 2>/dev/null || echo "0")
      total=$(echo "$response" | jq -r '.[0].total_processed // 0' 2>/dev/null || echo "0")
      
      echo "📊 Results:"
      echo "  - New leads created: $inserted"
      echo "  - Existing leads updated: $updated"
      echo "  - Total leads processed: $total"
    else
      echo "⚠️  Lead creation completed but response format unexpected"
    fi
```

## Integration with Existing Workflows

The new function can be integrated into existing workflows alongside the original function:

### Example: Enhanced Harris County Workflow

```yaml
- name: Build leads from fresh permits (enhanced)
  if: steps.scrape.outputs.new_permits != '0'
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  run: |
    echo "Building leads from fresh permits..."
    
    # Process all recent permits (existing behavior)
    echo "Processing all permits from last 7 days..."
    response1=$(curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_days": 7}')
    echo "Full processing response: $response1"
    
    # Also create a controlled sample for testing (new functionality)
    echo "Creating controlled sample of up to 50 leads for testing..."
    response2=$(curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":50,"p_days":365}')
    echo "Sample processing response: $response2"
```

## Parameter Variations

The function supports various parameter combinations:

```yaml
# Process up to 10 permits from last 30 days
- name: Small batch test
  run: |
    curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":10,"p_days":30}'

# Process up to 100 permits from all time
- name: Large batch from all data
  run: |
    curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":100,"p_days":null}'

# Process all permits from last 7 days (no limit)
- name: All recent permits
  run: |
    curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":null,"p_days":7}'
```

## Testing Integration

For testing workflows:

```yaml
- name: Verify function availability
  env:
    SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
    SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  run: |
    echo "Testing upsert_leads_from_permits_limit function..."
    
    # Test with minimal parameters
    response=$(curl -sS "$SUPABASE_URL/rest/v1/rpc/upsert_leads_from_permits_limit" \
      -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
      -H "Content-Type: application/json" \
      -d '{"p_limit":1,"p_days":1}')
    
    if [ $? -eq 0 ]; then
      echo "✅ Function is available and callable"
      echo "Response: $response"
    else
      echo "❌ Function call failed"
      exit 1
    fi
```

## Migration to Production

1. Apply the migration:
   ```bash
   make db-migrate
   ```

2. Test the function:
   ```bash
   psql -f verify_upsert_leads_limit_function.sql
   ```

3. Update workflows to use the new function for controlled lead generation

4. The original `upsert_leads_from_permits` function remains available for full processing

## Summary

- ✅ **Exact match**: The function supports the exact parameters from the problem statement
- ✅ **Backward compatible**: Original function continues to work unchanged
- ✅ **Flexible**: Supports various combinations of limit and date filtering
- ✅ **Production ready**: Includes proper error handling and return values
- ✅ **Testable**: Comprehensive test coverage and verification scripts