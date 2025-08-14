"use client";
import { useEffect, useState } from "react";

type Permit = {
  id: string;
  jurisdiction?: string | null;
  address?: string | null;
  trade?: string | null;
  status?: string | null;
  created_at?: string | null;
};

export default function PermitsPage() {
  const [permits, setPermits] = useState<Permit[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const r = await fetch("/api/permits/recent", { cache: "no-store" });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        setPermits(data?.permits ?? []);
      } catch (e: unknown) {
        // If you haven't implemented /api/permits/recent yet, this stays a graceful empty state.
        setErr(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="mx-auto max-w-7xl p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Permits</h1>
          <p className="text-sm text-slate-500">Track municipal permits related to your jobs.</p>
        </div>
        <button className="h-10 rounded-xl px-4 bg-indigo-600 text-white hover:bg-indigo-700" onClick={() => alert("Coming soon")}>
          Request Permit Search
        </button>
      </div>

      <div className="rounded-2xl border bg-white shadow-sm">
        <div className="px-6 py-4 border-b font-medium">Recent Permits</div>
        {err ? (
          <div className="p-6 text-rose-600 text-sm">Error: {err}</div>
        ) : loading ? (
          <div className="p-6 text-sm text-slate-500">Loading…</div>
        ) : permits.length === 0 ? (
          <div className="p-12 text-center">
            <div className="text-lg font-medium">No permits yet</div>
            <div className="mt-1 text-sm text-slate-500">
              Connect your permit provider or upload permit CSV to see them here.
            </div>
            <div className="mt-4 flex justify-center gap-2">
              <button className="h-10 rounded-xl px-4 border hover:bg-slate-50" onClick={() => alert("Connect provider…")}>
                Connect Provider
              </button>
              <button className="h-10 rounded-xl px-4 border hover:bg-slate-50" onClick={() => alert("Upload CSV…")}>
                Upload CSV
              </button>
            </div>
          </div>
        ) : (
          <ul className="divide-y">
            {permits.map((p) => (
              <li key={p.id} className="grid grid-cols-5 gap-4 px-6 py-4">
                <div className="font-medium truncate">{p.jurisdiction ?? "—"}</div>
                <div className="truncate">{p.address ?? "—"}</div>
                <div className="truncate">{p.trade ?? "—"}</div>
                <div className="truncate">{p.status ?? "—"}</div>
                <div className="text-right">
                  <button className="text-sm px-3 py-1.5 rounded-lg border hover:bg-slate-50">View</button>
                </div>
              </li>
            ))}
          <div>
            <div className="grid grid-cols-5 gap-4 px-6 py-3 border-b bg-slate-50 text-sm font-semibold text-slate-700">
              <div>Jurisdiction</div>
              <div>Address</div>
              <div>Trade</div>
              <div>Status</div>
              <div className="text-right">Actions</div>
            </div>
            <ul className="divide-y">
              {permits.map((p) => (
                <li key={p.id} className="grid grid-cols-5 gap-4 px-6 py-4">
                  <div className="font-medium truncate">{p.jurisdiction ?? "—"}</div>
                  <div className="truncate">{p.address ?? "—"}</div>
                  <div className="truncate">{p.trade ?? "—"}</div>
                  <div className="truncate">{p.status ?? "—"}</div>
                  <div className="text-right">
                    <button className="text-sm px-3 py-1.5 rounded-lg border hover:bg-slate-50">View</button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}