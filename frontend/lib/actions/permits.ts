// Server action to fetch leads using a similar pattern to the original permits action
import { createSupabaseServerClient } from '@/lib/supabase/server';
import type { LeadForPermitsView, LeadsApiResponse } from '@/types';

export async function getLeads(): Promise<LeadsApiResponse> {
  try {
    // Query leads table instead of permits, mapping fields appropriately
    const supabase = createSupabaseServerClient();
    const { data: leads, error } = await supabase
      .from('leads')
      .select('id, city, county, service, value, status, created_at, address')
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