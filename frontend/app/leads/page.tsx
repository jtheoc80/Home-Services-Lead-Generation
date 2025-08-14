"use client";

import { useEffect, useMemo, useState, useTransition } from "react";

type Lead = {
  id: string;
  name: string;
  email?: string | null;
  phone?: string | null;
  service?: string | null; // aka trade
  county?: string | null;
  status?: "New" | "Qualified" | "Contacted" | "Won" | "Lost" | string | null;
  created_at?: string | null;
};

const statusStyles: Record<string, string> = {
  New: "bg-sky-50 text-sky-700 ring-1 ring-sky-200",
  Qualified: "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  Contacted: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  Won: "bg-indigo-50 text-indigo-700 ring-1 ring-indigo-200",
  Lost: "bg-rose-50 text-rose-700 ring-1 ring-rose-200",
};

function Badge({ value }: { value?: string | null }) {
  if (!value) return null;
  const cls = statusStyles[value] ?? "bg-slate-100 text-slate-700 ring-1 ring-slate-200";
  return <span className={`px-2 py-1 text-xs font-medium rounded-full ${cls}`}>{value}</span>;
}

function Avatar({ name }: { name?: string | null }) {
  const initials = (name ?? "?")
    .split(/\s+/)
    .slice(0, 2)
    .map((n) => n[0]?.toUpperCase() ?? "")
    .join("");
  return (
    <div className="size-8 rounded-full bg-gradient-to-br from-indigo-500 to-sky-500 text-white grid place-items-center text-xs font-semibold">
      {initials || "LL"}
    </div>
  );
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState<string>("All");
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch("/api/leads/recent", { cache: "no-store" });
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const body = await res.json();
        // API returns { data: Lead[], ... } but we need to map to our Lead type
        const apiLeads = body?.data ?? [];
        const mappedLeads = apiLeads.map((lead: any) => ({
          id: String(lead.id),
          name: lead.name,
          email: lead.email,
          phone: lead.phone,
          service: lead.source, // Map source to service for now
          county: lead.city, // Map city to county for now
          status: lead.status,
          created_at: lead.created_at,
        }));
        setLeads(mappedLeads);
      } catch (e: any) {
        setErr(e?.message ?? "Failed to load leads");
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const filtered = useMemo(() => {
    const term = q.trim().toLowerCase();
    return (leads ?? []).filter((l) => {
      const passStatus = status === "All" || (l.status ?? "") === status;
      const hay = `${l.name ?? ""} ${l.email ?? ""} ${l.phone ?? ""} ${l.service ?? ""} ${l.county ?? ""}`.toLowerCase();
      return passStatus && (term === "" || hay.includes(term));
    });
  }, [leads, q, status]);

  return (
    <div className="mx-auto max-w-7xl p-6 space-y-6">
      {/* Sticky header */}
      <div className="sticky top-0 z-10 -mx-6 px-6 py-4 bg-white/70 backdrop-blur border-b">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Leads</h1>
            <p className="text-sm text-slate-500">Manage your pipeline in Lead Ledger Pro.</p>
          </div>
          <div className="flex items-center gap-2">
            <input
              value={q}
              onChange={(e) => startTransition(() => setQ(e.target.value))}
              placeholder="Search name, email, county…"
              className="h-10 w-64 rounded-xl border px-3 text-sm outline-none focus:ring-2 ring-sky-200"
            />
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="h-10 rounded-xl border px-3 text-sm outline-none focus:ring-2 ring-sky-200"
            >
              {["All", "New", "Qualified", "Contacted", "Won", "Lost"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            <button
              className="h-10 rounded-xl px-4 text-sm font-medium bg-indigo-600 text-white hover:bg-indigo-700"
              onClick={() => router.push("/leads/new")}
            >
              Add Lead
            </button>
          </div>
        </div>
      </div>

      {/* Card */}
      <div className="rounded-2xl border shadow-sm bg-white">
        {/* Table head */}
        <div className="grid grid-cols-6 px-6 py-3 text-xs font-medium text-slate-500">
          <div className="col-span-2">Name</div>
          <div>Trade</div>
          <div>County</div>
          <div>Status</div>
          <div className="text-right">Actions</div>
        </div>
        <div className="h-px bg-slate-100" />

        {/* States */}
        {loading ? (
          <div className="p-6 text-sm text-slate-500">Loading leads…</div>
        ) : err ? (
          <div className="p-6 text-sm text-rose-600">Error: {err}</div>
        ) : filtered.length === 0 ? (
          <div className="p-10 text-center text-slate-500">
            No leads match your filters. Try clearing the search or add a new lead.
          </div>
        ) : (
          <ul className="divide-y">
            {filtered.map((l) => (
              <li key={l.id} className="grid grid-cols-6 items-center px-6 py-4">
                <div className="col-span-2 flex items-center gap-3">
                  <Avatar name={l.name} />
                  <div>
                    <div className="font-medium">{l.name ?? "—"}</div>
                    <div className="text-xs text-slate-500">
                      {l.email ?? "—"} · {l.phone ?? "—"}
                    </div>
                  </div>
                </div>
                <div className="truncate">{l.service ?? "—"}</div>
                <div className="truncate">{l.county ?? "—"}</div>
                <div><Badge value={l.status ?? "New"} /></div>
                <div className="text-right">
                  <button
                    className="text-sm px-3 py-1.5 rounded-lg border hover:bg-slate-50"
                    onClick={() => router.push(`/leads/${l.id}`)}
                  >
                    View
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Bottom toolbar */}
      <div className="flex justify-end gap-2">
        <button className="h-10 rounded-xl px-4 border hover:bg-slate-50" onClick={() => location.reload()}>
          Refresh
        </button>
        <button className="h-10 rounded-xl px-4 bg-slate-900 text-white hover:bg-black/90" onClick={() => (location.href = "/permits")}>
          Go to Permits
        </button>
      </div>
    </div>
  );
}