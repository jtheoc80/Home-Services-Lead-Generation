import { createServiceClient } from "@/lib/supabase/server";
import DashboardClient from "@/components/DashboardClient";

export const dynamic = 'force-dynamic'
export const revalidate = 0

async function fetchLeads() {
  try {
    const supabase = createServiceClient();
    const { data: leads, error } = await supabase
      .from('leads')
      .select('id, name, trade, county, status, value, lead_score, created_at, address, zipcode')
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

export default async function Dashboard() {
  const { leads, error } = await fetchLeads();
  
  // Show error state with actual DB error message
  if (error) {
    return <pre className="p-6 text-red-600">DB error: {error}</pre>;
  }
  
  return <DashboardClient leads={leads || []} initialError={error} />;
}
