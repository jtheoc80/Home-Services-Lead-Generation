import { createServiceClient } from "@/lib/supabase/server";
import LeadsClient from "@/components/LeadsClient";

export const dynamic = 'force-dynamic'
export const revalidate = 0

async function fetchLeads() {
  try {
    const supabase = createServiceClient();
    const { data: leads, error } = await supabase
      .from('leads')
      .select('id, name, trade, county, status, value, lead_score, created_at, email, phone, service, address, city, state, zip, permit_id')
      .order('created_at', { ascending: false });
    
    if (error) {
      console.error('Database error:', error);
      return { leads: null, error: error.message };
    }
    
    return { leads: leads || [], error: null };
  } catch (error: any) {
    console.error('Fetch error:', error);
    return { leads: null, error: error.message || 'Unknown error' };
  }
}

export default async function LeadsPage() {
  const { leads, error } = await fetchLeads();
  
  // Show error state with actual DB error message
  if (error) {
    return <pre className="p-6 text-red-600">DB error: {error}</pre>;
  }
  
  return <LeadsClient leads={leads || []} initialError={error} />;
}