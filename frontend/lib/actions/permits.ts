// Server action to fetch permits using the exact query from the problem statement
import { createSupabaseServerClient } from '@/lib/supabase/server';

// Types for permits data based on the problem statement query
export interface Permit {
  id: string;
  jurisdiction: string;
  county: string;
  permit_type: string;
  value: number | null;
  status: string;
  issued_date: string;
  address: string;
}

export async function getPermits(): Promise<{ data: Permit[] | null; error: any }> {
  try {
    // This is the exact query from the problem statement
    const supabase = createSupabaseServerClient();
    const { data: permits, error } = await supabase
      .from('permits')
      .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
      .order('issued_date', { ascending: false })
      .limit(50);

    return { data: permits, error };
  } catch (err) {
    console.error('Error fetching permits:', err);
    return { 
      data: null, 
      error: err instanceof Error ? err.message : 'Failed to fetch permits'
    };
  }
}