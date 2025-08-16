export const dynamic = 'force-dynamic'
export const revalidate = 0

import { createServerSupabase } from '@/lib/supabase/clients'

export default async function LeadsPage() {
  const sb = createServerSupabase()
  const { data, error } = await sb
    .from('leads')
    .select('id,name,trade,county,status,lead_score,created_at')
    .order('created_at', { ascending: false })
    .limit(50)

  if (error) return <pre>{error.message}</pre>
  if (!data?.length) return <p>No leads yet.</p>

  return (
    <ul>
      {data.map(l => (
        <li key={l.id}>{l.name} · {l.trade} · {l.county} · {l.status}</li>
      ))}
    </ul>
  )
}