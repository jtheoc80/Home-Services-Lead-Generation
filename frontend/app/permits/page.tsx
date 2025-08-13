import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";

export default function PermitsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Permits</h1>
        <div className="flex gap-2">
          <Button variant="ghost">Search</Button>
          <Button variant="ghost">Filter</Button>
        </div>
      </div>

      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">Recent Permits</h2>
        <div className="text-sm text-gray-600">
          Recent permits + search will be wired here. Link to detail pages coming soon.
        </div>
      </Card>
    </div>
  );
}