'use client';

import { useLeads } from '@/hooks/useLeads';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';

export default function LeadsPage() {
  const { leads, error } = useLeads();

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Leads</h1>
        <div className="flex gap-2">
          <Button variant="ghost">Filter</Button>
          <Button>Add Lead</Button>
        </div>
      </div>

      <Card>
        {!leads && !error && <div className="p-6 text-sm text-muted-foreground">Loading…</div>}
        {error && <div className="p-6 text-sm text-red-600">{error}</div>}
        {leads && leads.length === 0 && (
          <div className="p-6 text-sm text-muted-foreground">No leads yet.</div>
        )}

        {leads && leads.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="px-4 py-3 text-left">Name</th>
                  <th className="px-4 py-3 text-left">Trade</th>
                  <th className="px-4 py-3 text-left">County</th>
                  <th className="px-4 py-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {leads.map((l) => (
                  <tr key={l.id} className="border-b last:border-0">
                    <td className="px-4 py-3">{l.name}</td>
                    <td className="px-4 py-3">{l.trade}</td>
                    <td className="px-4 py-3">{l.county}</td>
                    <td className="px-4 py-3">{l.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}