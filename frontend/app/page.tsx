import Card from "@/components/ui/Card";

const stats = [
  { label: "New Leads", value: "24" },
  { label: "Qualified", value: "11" },
  { label: "Contacted", value: "8" },
  { label: "Won", value: "3" }
];

export default async function DashboardPage() {
  // server component: fetch precomputed stats later from your API
  return (
    <div className="space-y-6">
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(s => (
          <Card key={s.label} className="p-4">
            <div className="text-xs text-gray-500">{s.label}</div>
            <div className="mt-2 text-2xl font-semibold">{s.value}</div>
          </Card>
        ))}
      </section>

      <section>
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Recent Leads</h2>
            <a href="/leads" className="text-brand-600 text-sm">View all</a>
          </div>
          <div className="mt-4 text-sm text-gray-600">
            Wire this to Supabase later; show 10 newest leads here.
          </div>
        </Card>
      </section>
    </div>
  );
}