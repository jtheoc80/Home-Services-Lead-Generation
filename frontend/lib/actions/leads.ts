
// Server action to fetch leads using the exact schema from the leads table
import { createServerSupabase } from '@/lib/supabase/clients';
import type { Lead } from '@/types/supabase';

// Re-export the Lead type for convenience
export type { Lead } from '@/types/supabase';

export async function getLeads(): Promise<{ data: Lead[] | null; error: string | null }> {
  try {
    // Query leads table with relevant fields for the demo
    const supabase = createServerSupabase();
    const { data: leads, error } = await supabase
      .from('leads')
      .select('id, name, phone, email, address, city, state, county, status, source, lead_score, value, created_at')

      .order('created_at', { ascending: false })
      .limit(50);

    return { data: leads, error: error?.message || null };
  } catch (err) {
    console.error('Error fetching leads:', err);
    return { 
      data: null, 
      error: err instanceof Error ? err.message : 'Failed to fetch leads'
    };
  }
}