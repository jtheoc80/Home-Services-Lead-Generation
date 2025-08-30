import { createClient } from '@supabase/supabase-js';
const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!url || !anon) { if (process.env.NODE_ENV !== 'production') throw new Error('Missing NEXT_PUBLIC_SUPABASE_*'); }


if (!url || !anon) {
  throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY');
}


export const supabase = createClient(url, anon);