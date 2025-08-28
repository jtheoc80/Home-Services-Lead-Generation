import { createClient } from '@supabase/supabase-js';

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const anon = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

let supabase;
if (!url || !anon) {
  if (process.env.NODE_ENV !== 'production') {
    throw new Error('Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY');
  } else {
    console.warn('Supabase env not set in production');
    supabase = undefined;
  }
} else {
  supabase = createClient(url, anon);
}

export { supabase };