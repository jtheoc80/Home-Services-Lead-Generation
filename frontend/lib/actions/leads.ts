// Server action to fetch leads using the exact query from the problem statement
import { createSupabaseServerClient } from '@/lib/supabase/server';
import type { LeadForPermitsView, LeadsApiResponse } from '@/types';

export async function getLeads(): Promise<LeadsApiResponse> {
  try {
    // Query leads with fields that map to the permits demo structure
    const supabase = createSupabaseServerClient();
    const { data: leads, error } = await supabase
      .from('leads')
      .select('id, created_at, name, email, phone, address, city, state, county, status, service, value, source')
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