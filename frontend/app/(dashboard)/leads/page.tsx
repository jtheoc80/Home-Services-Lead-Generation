export const dynamic = 'force-dynamic'
export const revalidate = 0

import { createServerSupabase } from '@/lib/supabase/clients'
import LeadsPageClient from './LeadsPageClient'

export default async function LeadsPage() {
  const sb = await createServerSupabase()
  const { data, error } = await sb
    .from('leads')
    .select('id, name, owner_name, contractor_name, lead_type, trade, county, status, lead_score, score_label, created_at, address, zipcode, value, external_permit_id, phone, email')
    .order('created_at', { ascending: false })
    .limit(100)

  return <LeadsPageClient leads={data || []} error={error?.message} />
}
