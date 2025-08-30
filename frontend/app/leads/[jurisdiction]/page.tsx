import { supabase } from "@/src/lib/supabaseClient";

export default async function Leads({ params }: { params: { jurisdiction: string }}) {
  const j = decodeURIComponent(params.jurisdiction);
  const { data, error } = await supabase
    .from("public_leads")
    .select("*")
    .eq("jurisdiction", j)
    .order("created_at", { ascending: false })
    .limit(50);

  if (error) throw new Error(error.message);

  return (
    <main className="p-6">
      <h1 className="text-2xl font-bold">Permits — {j}</h1>
      <ul className="mt-4 space-y-2">
        {(data ?? []).map((r: { id: string; source: string; source_record_id: string; jurisdiction: string }) => (
          <li key={r.id} className="border p-3 rounded">
            <div className="font-medium">{r.source} — {r.source_record_id}</div>
            <div className="text-sm opacity-70">Jurisdiction: {r.jurisdiction}</div>
          </li>
        ))}
      </ul>
    </main>
  );
}