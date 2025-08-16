# Permits View Implementation

This document describes the implementation of the `permits` view to support the Supabase query pattern from the problem statement.

## Problem Statement

The codebase needed to support this Supabase query:

```typescript
const supabase = createSupabaseServerClient()
const { data: permits, error } = await supabase
  .from('permits')
  .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
  .order('issued_date', { ascending: false })
  .limit(50)
```

## Solution

Created a `public.permits` view that maps the existing `gold.permits` table columns to the expected schema.

### Column Mapping

| Expected Column | Source Column | Source Table | Notes |
|----------------|---------------|--------------|--------|
| `id` | `id` | `gold.permits` | Direct mapping |
| `jurisdiction` | `s.name` or `s.id` | `meta.sources` | Joined from source registry |
| `county` | `county` | `gold.permits` | Direct mapping |
| `permit_type` | `permit_type` | `gold.permits` | Direct mapping |
| `value` | `valuation` | `gold.permits` | Column alias |
| `status` | `status` | `gold.permits` | Direct mapping |
| `issued_date` | `issued_at` | `gold.permits` | Column alias |
| `address` | `address` | `gold.permits` | Direct mapping |

### Files Created

1. **`sql/create_permits_view.sql`** - SQL migration to create the permits view
2. **`frontend/app/demo/permits/page.tsx`** - Demo page testing the exact query
3. **`frontend/lib/actions/permits.ts`** - Server action with proper TypeScript types
4. **`scripts/test_permits_view.ts`** - Test script to validate the implementation

## Database Dependencies

The permits view requires these database components to be set up:

1. **`gold.permits` table** - Created by `2025-setup.sql`
2. **`meta.sources` table** - Created by `2025-setup.sql` 
3. **`public.permits` view** - Created by `create_permits_view.sql`

## Usage Examples

### Client-Side Query (Browser)
```typescript
import { supabase } from '@/lib/supabaseClient';

const { data: permits, error } = await supabase
  .from('permits')
  .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
  .order('issued_date', { ascending: false })
  .limit(50);
```

### Server-Side Query (Server Actions)
```typescript
import { createSupabaseServerClient } from '@/lib/supabase/server';

const supabase = createSupabaseServerClient();
const { data: permits, error } = await supabase
  .from('permits')
  .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
  .order('issued_date', { ascending: false })
  .limit(50);
```

### Using the Server Action
```typescript
import { getPermits } from '@/lib/actions/permits';

const { data: permits, error } = await getPermits();
```

## Testing

Run the validation test:

```bash
tsx scripts/test_permits_view.ts
```

This test validates:
- The permits view exists and is accessible
- All expected columns are present
- The exact problem statement query works
- Query performance is acceptable
- Data structure matches TypeScript interface

## Demo Page

Visit `/demo/permits` to see the implementation in action. This page:
- Uses the exact query from the problem statement
- Shows all expected columns in a table
- Displays statistics about the data
- Handles error states gracefully
- Provides technical implementation details

## Row Level Security

The permits view inherits RLS from the underlying `gold.permits` table:
- Authenticated users can read permits data
- Service role can read/write permits data
- Anonymous access is granted for public demo purposes

## Performance Considerations

The view includes:
- Proper indexing on `gold.permits.issued_at` for ordering
- Efficient JOIN with `meta.sources` table
- LIMIT clauses to prevent large data transfers
- Optimized column selection

## Troubleshooting

### "Table 'permits' doesn't exist"
- Ensure `create_permits_view.sql` has been applied
- Verify `2025-setup.sql` has been run first

### "Missing columns" errors
- Check that `gold.permits` table has all expected columns
- Verify the view definition matches the schema

### Permission errors
- Ensure RLS policies are properly configured
- Check that user has appropriate role (authenticated/service_role)
- Verify GRANTS on the view

### No data returned
- Check if `gold.permits` table has data
- Verify the `meta.sources` table is populated
- Ensure `issued_at` is not null (filtered in view)

## Future Enhancements

Potential improvements:
1. Add materialized view for better performance
2. Include computed lead scoring in the view
3. Add geospatial queries for location-based filtering
4. Implement caching layer for frequently accessed data