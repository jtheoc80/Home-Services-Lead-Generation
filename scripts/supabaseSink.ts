import { createClient } from "@supabase/supabase-js";

export type Permit = {
  source_system: string;   // e.g. "city_of_houston"
  permit_id: string;
  issue_date: string;      // ISO (or 'YYYY-MM-DD')
  trade?: string;
  address?: string;
  zipcode?: string;
  valuation?: number | null;
  contractor?: string | null;
};

const url = process.env.SUPABASE_URL!;
const key = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const sb = createClient(url, key, { auth: { persistSession: false } });

export async function upsertPermits(rows: Permit[], chunk = 500) {
  let upserted = 0;
  for (let i = 0; i < rows.length; i += chunk) {
    const batch = rows.slice(i, i + chunk);
    const { error, count } = await sb
      .from("permits")
      .upsert(batch, { onConflict: "source_system,permit_id", ignoreDuplicates: false, count: "estimated" });
    if (error) throw error;
    upserted += count ?? batch.length; // supabase-js may not return count—fallback
  }
  return upserted;
}