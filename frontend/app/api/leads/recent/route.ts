import { NextResponse } from "next/server";
import { getSupabaseClient } from "../../../lib/supabaseServer";

// 1) Try your Python backend first (via proxy)
async function fetchFromBackend() {
  const base = process.env.LEAD_API_BASE_URL;
  if (!base) return null;

  const res = await fetch(`${base}/api/leads/recent`, {
    headers: {
      "Content-Type": "application/json",
      ...(process.env.LEAD_API_KEY ? { Authorization: `Bearer ${process.env.LEAD_API_KEY}` } : {}),
    },
    // In server routes this runs on Node; no need for cache
  });

  if (!res.ok) throw new Error(`Backend responded ${res.status}`);
  const body = await res.json();
  // Expect either {leads: [...] } or just array
  return Array.isArray(body) ? body : body?.leads ?? [];
}

// 2) Fallback to Supabase if backend isn't set/ready
async function fetchFromSupabase() {
  try {
    // Use service role to bypass RLS and fetch all leads without user filtering
    const supabase = getSupabaseClient({ useServiceRole: true });
    const { data, error } = await supabase
      .from("leads")
      .select("id,name,email,phone,service,county,status,created_at,source,address,city,state,zip,metadata")
      .order("created_at", { ascending: false })
      .limit(50);

    if (error) throw error;
    return data ?? [];
  } catch (error) {
    console.error('Supabase fetch error:', error);
    return [];
  }
}

export async function GET() {
  try {
    const fromBackend = await fetchFromBackend();
    const leads = fromBackend ?? (await fetchFromSupabase());
    return NextResponse.json({ leads, data: leads }, { status: 200 });
  } catch (err: any) {
    return NextResponse.json({ error: err?.message ?? "Server error" }, { status: 500 });
  }
}