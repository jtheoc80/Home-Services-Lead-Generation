'use client';

import { useState } from 'react';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';

type Permit = {
  id: string;
  address: string;
  trade: string;
  status: string;
  submitted_at?: string | null;
};

export default function PermitsPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<Permit[]>([]);
  const [recent, setRecent] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  async function searchPermits(e?: React.FormEvent) {
    e?.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      // TODO: wire to your real backend/scraper
      const mock: Permit[] = [
        { id: query, address: query, trade: 'Roofing', status: 'Submitted', submitted_at: new Date().toISOString() },
      ];
      setResults(mock);
      setRecent((prev) => [query, ...prev.filter((q) => q !== query)].slice(0, 5));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-semibold tracking-tight">Permits</h1>
      </div>

      <Card className="p-4">
        <form onSubmit={searchPermits} className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search address, permit #, or county…"
            className="flex-1 rounded-xl border px-3 py-2 outline-none focus:ring"
          />
          <Button type="submit" disabled={loading}>
            {loading ? 'Searching…' : 'Search'}
          </Button>
        </form>
      </Card>

      {results.length > 0 && (
        <Card className="overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50">
              <tr className="[&>th]:px-4 [&>th]:py-3 text-left text-gray-500 font-medium">
                <th>Address</th><th>Trade</th><th>Status</th><th>Submitted</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {results.map((r) => (
                <tr key={r.id} className="[&>td]:px-4 [&>td]:py-3">
                  <td className="font-medium">{r.address}</td>
                  <td>{r.trade}</td>
                  <td>{r.status}</td>
                  <td>{r.submitted_at ? new Date(r.submitted_at).toLocaleDateString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {recent.length > 0 && (
        <div>
          <h2 className="text-sm font-medium text-gray-500 mb-2">Recent searches</h2>
          <ul className="flex flex-wrap gap-2">
            {recent.map((q) => (
              <li key={q}>
                <button
                  onClick={() => {
                    setQuery(q);
                    // run a search immediately when clicking a chip
                    void searchPermits(undefined, q);
                  }}
                  className="rounded-full border px-3 py-1 text-sm hover:bg-gray-50"
                >
                  {q}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}