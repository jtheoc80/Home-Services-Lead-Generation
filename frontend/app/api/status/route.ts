import { NextResponse } from "next/server";

export async function GET() {
  const base = process.env.LEAD_API_BASE_URL;
  const hasSB = !!(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
  const backend: { ok: boolean; count?: number; status?: number; error?: string } = { ok: false };

  if (base) {
    try {
      const r = await fetch(`${base}/api/leads/recent`, {
        headers: process.env.LEAD_API_KEY ? { Authorization: `Bearer ${process.env.LEAD_API_KEY}` } : {},
        cache: "no-store",
      });
      backend.status = r.status;
      if (r.ok) {
        const data = await r.json();
        const arr = Array.isArray(data) ? data : data?.leads ?? [];
        backend.ok = true;
        backend.count = arr.length ?? 0;
      } else {
        backend.error = await r.text();
      }
    } catch (e: unknown) {
      backend.error = e instanceof Error ? e.message : "request failed";
    }
  }

  return NextResponse.json({
    env: {
      LEAD_API_BASE_URL: !!base,
      LEAD_API_KEY: !!process.env.LEAD_API_KEY,
      SUPABASE_SET: hasSB,
    },
    backend,
  });
}