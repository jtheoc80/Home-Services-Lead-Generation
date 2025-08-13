"use client";

import LeadTable from "@/components/data/LeadTable";
import Card from "@/components/ui/Card";
import Button from "@/components/ui/Button";

// Mock data - replace with real data from API later
const mockLeads = [
  {
    id: "1",
    name: "John Smith",
    trade: "Roofing",
    county: "Harris",
    status: "New" as const
  },
  {
    id: "2", 
    name: "Jane Doe",
    trade: "HVAC",
    county: "Montgomery",
    status: "Qualified" as const
  },
  {
    id: "3",
    name: "Bob Johnson", 
    trade: "Electrical",
    county: "Fort Bend",
    status: "Contacted" as const
  }
];

export default function LeadsPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Leads</h1>
        <div className="flex gap-2">
          <Button variant="ghost">Filter</Button>
          <Button>Add Lead</Button>
        </div>
      </div>

      <Card className="p-0">
        <LeadTable data={mockLeads} />
      </Card>
    </div>
  );
}