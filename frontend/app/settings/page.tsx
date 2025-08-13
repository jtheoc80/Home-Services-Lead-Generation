import Card from "@/components/ui/Card";
import Card from "../../components/ui/Card";
import Button from "../../components/ui/Button";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Settings</h1>

      <div className="grid gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Company Profile</h2>
          <div className="text-sm text-gray-600">
            Company information and team settings will be configured here.
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold mb-4">Integrations</h2>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">Stripe</h3>
                <p className="text-sm text-gray-600">Payment processing integration</p>
              </div>
              <Button variant="ghost">Configure</Button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-medium">Supabase</h3>
                <p className="text-sm text-gray-600">Database and authentication</p>
              </div>
              <Button variant="ghost">Configure</Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}