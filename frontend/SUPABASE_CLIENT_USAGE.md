# Browser-Safe Supabase Client Export

This implementation provides a simple, direct export of a Supabase client instance that is safe for browser use.

## Usage

```typescript
import { supabase } from '@/lib/supabaseClient';

// Use directly in your components
const { data, error } = await supabase
  .from('leads')
  .insert([{ name: "Client", source: "client" }]);
```

## Implementation

The client is exported as a constant using the anonymous key:

```typescript
// "browser client" only – safe to use with anon key
export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
```

## Requirements

- `NEXT_PUBLIC_SUPABASE_URL` - Your Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Your Supabase anonymous key

## Browser Safety

This client uses only browser-safe environment variables (prefixed with `NEXT_PUBLIC_`) and the anonymous key, making it suitable for client-side usage.

## Dynamic Import (for build-time safety)

If your page is statically generated and you encounter build-time issues, use dynamic imports:

```typescript
const handleAction = async () => {
  const { supabase } = await import('@/lib/supabaseClient');
  const { data, error } = await supabase.from('table').select('*');
};
```

## Backward Compatibility

The existing `getSupabase()` function remains available for more advanced use cases with error handling and server-side safety checks.