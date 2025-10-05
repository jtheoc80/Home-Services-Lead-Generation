export const dynamic = 'force-dynamic'
export const revalidate = 0

import { createServerSupabase } from '@/lib/supabase/clients'
import LeadsPageClient from './LeadsPageClient'

export default async function LeadsPage() {
  const sb = await createServerSupabase()
  
  // Temporarily exclude new columns until PostgREST cache refreshes
  const { data, error } = await sb
    .from('leads')
    .select('id, name, trade, county, status, lead_score, score_label, created_at, address, zipcode, value, external_permit_id, phone, email')
    .order('created_at', { ascending: false })
    .limit(100)

  // Add placeholder values for new columns
  const leadsWithPlaceholders = data?.map(lead => ({
    ...lead,
    owner_name: lead.name, // Use name as fallback
    contractor_name: null,
    lead_type: 'unknown'
  }))

  return <LeadsPageClient leads={leadsWithPlaceholders || []} error={error?.message} />
}
