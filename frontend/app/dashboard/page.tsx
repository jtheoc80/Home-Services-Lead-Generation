"use client";

import { useEffect, useMemo, useState } from "react";
import { Lead } from "@/types/supabase";

function Stat({ label, value, hint }: { label: string; value: string | number; hint?: string }) {
  return (
    <div className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="text-sm text-slate-500">{label}</div>
      <div className="mt-1 text-2xl font-semibold tracking-tight">{value}</div>
      {hint ? <div className="text-xs text-slate-400 mt-1">{hint}</div> : null}
    </div>
  );
}

export default function Dashboard() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch("/api/leads/recent", { cache: "no-store" });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        setLeads(data?.leads ?? []);
      } catch (e: unknown) {
        setErr(e instanceof Error ? e.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const stats = useMemo(() => {
    const total = leads.length;
    const newCount = leads.filter((l) => (l.status ?? "").toLowerCase() === "new").length;
    const qualified = leads.filter((l) => (l.status ?? "").toLowerCase() === "qualified").length;
    const won = leads.filter((l) => (l.status ?? "").toLowerCase() === "won").length;
    return { total, newCount, qualified, won };
  }, [leads]);

  return (
    <div className="mx-auto max-w-7xl p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Lead Ledger Pro</h1>
        <p className="text-sm text-slate-500">Overview of your pipeline at a glance.</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Total Leads" value={loading ? "—" : stats.total} />
        <Stat label="New" value={loading ? "—" : stats.newCount} />
        <Stat label="Qualified" value={loading ? "—" : stats.qualified} />
        <Stat label="Won" value={loading ? "—" : stats.won} />
      </div>

      {/* Recent leads */}
      <div className="rounded-2xl border bg-white shadow-sm">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div className="font-medium">Recent Leads</div>
          <button className="h-9 rounded-xl px-3 text-sm border hover:bg-slate-50" onClick={() => (location.href = "/leads")}>
            View all
          </button>
        </div>

        {err ? (
          <div className="p-6 text-rose-600 text-sm">Error: {err}</div>
        ) : loading ? (
          <div className="p-6 text-sm text-slate-500">Loading…</div>
        ) : leads.length === 0 ? (
          <div className="p-10 text-center text-slate-500">No leads yet. Add one to get started.</div>
        ) : (
          <ul className="divide-y">
            {leads.slice(0, 8).map((l) => (
              <li key={l.id} className="flex items-center justify-between px-6 py-4">
                <div className="min-w-0">
                  <div className="font-medium truncate">{l.name ?? "—"}</div>
                  <div className="text-xs text-slate-500 truncate">{l.service ?? "—"} · {l.county ?? "—"}</div>
                </div>
                <div className="text-xs">
                  <span className="px-2 py-1 rounded-full bg-slate-100 ring-1 ring-slate-200">{l.status ?? "New"}</span>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}