"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useEnhancedLeads } from "@/hooks/useLeads";
import { useAuth } from "@/components/AuthGuard";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import LeadScore from "@/components/ui/LeadScore";
import MetricsCards from "@/components/MetricsCards";
import LeadCard from "@/components/LeadCard";
import TexasCountySelector from "@/components/ui/TexasCountySelector";
import DashboardHeader from "@/components/ui/DashboardHeader";
import { 
  Users, 
  TrendingUp, 
  Target, 
  Trophy, 
  Clock, 
  MapPin,
  Filter,
  Search,
  ChevronRight,
  AlertCircle,
  LogOut,
  User
} from "lucide-react";

function DashboardContent() {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const { leads, error, loading } = useEnhancedLeads();
  const [selectedCounties, setSelectedCounties] = useState<string[]>(['harris', 'fortbend']);
  const [searchTerm, setSearchTerm] = useState('');

  const stats = useMemo(() => {
    if (!leads) return { total: 0, newCount: 0, qualified: 0, won: 0, avgScore: 0, totalValue: 0 };
    
    const filteredLeads = leads.filter(lead => 
      selectedCounties.length === 0 ||
      selectedCounties.some(county => 
        lead.county?.toLowerCase().includes(county)
      )
    );
    
    const total = filteredLeads.length;
    const newCount = filteredLeads.filter((l) => (l.status ?? "").toLowerCase() === "new").length;
    const qualified = filteredLeads.filter((l) => (l.status ?? "").toLowerCase() === "qualified").length;
    const won = filteredLeads.filter((l) => (l.status ?? "").toLowerCase() === "won").length;
    
    // Use the new lead_score field from database, with fallback to computed score
    const avgScore = filteredLeads.reduce((sum, l) => sum + (l.lead_score || l.score || 0), 0) / total || 0;
    
    // Use the new value field from database, with fallback to computed permitValue
    const totalValue = filteredLeads.reduce((sum, l) => sum + (l.value || l.permitValue || 0), 0);
    
    return { total, newCount, qualified, won, avgScore, totalValue };
  }, [leads, selectedCounties]);

  const filteredLeads = useMemo(() => {
    if (!leads) return [];
    
    return leads.filter(lead => {
      const matchesCounty = selectedCounties.length === 0 || 
        selectedCounties.some(county => 
          lead.county?.toLowerCase().includes(county)
        );
      const matchesSearch = !searchTerm || 
        lead.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.service?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.tradeType?.toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesCounty && matchesSearch;
    });
  }, [leads, selectedCounties, searchTerm]);

  // Show error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
        <div className="mx-auto max-w-7xl p-6">
          <div className="flex items-center justify-center min-h-[60vh]">
            <Card className="p-8 max-w-lg text-center">
              <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Database Connection Error</h2>
              <p className="text-gray-600 mb-4">{error}</p>
              <div className="text-sm text-gray-500 space-y-2">
                <p>To connect to your Supabase database:</p>
                <ol className="list-decimal list-inside text-left space-y-1">
                  <li>Copy your Supabase project URL and anon key</li>
                  <li>Update .env.local with your credentials</li>
                  <li>Ensure your Supabase database has the 'leads' table</li>
                  <li>Restart the development server</li>
                </ol>
              </div>
            </Card>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="mx-auto max-w-7xl p-6 space-y-8">
        <DashboardHeader
          title="Texas Lead Dashboard"
          subtitle="Intelligent home services lead generation across the Lone Star State"
        />

        {/* Stats Grid */}
        <MetricsCards
          totalLeads={stats.total}
          totalValue={stats.totalValue}
          averageScore={stats.avgScore}
          newLeads={stats.newCount}
          loading={loading}
        />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - County Selector */}
          <div className="lg:col-span-1">
            <TexasCountySelector
              selectedCounties={selectedCounties}
              onCountyChange={setSelectedCounties}
              showStats={true}
            />
          </div>

          {/* Right Column - Recent Leads */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-brand-600" />
                  <h3 className="text-xl font-semibold text-gray-900">Recent Leads</h3>
                </div>
                
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search leads..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                  <button className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    <Filter className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {loading ? (
                <div className="space-y-4">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="h-20 bg-gray-100 rounded-lg"></div>
                    </div>
                  ))}
                </div>
              ) : filteredLeads.length === 0 ? (
                <div className="p-10 text-center text-gray-500">
                  <MapPin className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-medium mb-2">No leads found</h3>
                  <p>
                    {leads && leads.length === 0 
                      ? "No leads in the database yet. Try adding some test data."
                      : "Try adjusting your county selection or search terms."
                    }
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredLeads.slice(0, 5).map((lead) => (
                    <LeadCard
                      key={lead.id}
                      lead={lead}
                      compact={true}
                      showFeedback={false}
                    />
                  ))}

                  <div className="mt-6 text-center">
                    <button
                      onClick={() => router.push("/leads")}
                      className="inline-flex items-center px-6 py-3 bg-brand-600 text-white font-medium rounded-xl hover:bg-brand-700 transition-colors duration-200 shadow-soft"
                    >
                      View All Leads
                      <ChevronRight className="w-4 h-4 ml-2" />
                    </button>
                  </div>
                </div>
              )}
            </Card>
          </div>
          
          {/* User Info Panel */}
          {user && (
            <div className="mt-8">
              <Card className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="bg-blue-100 p-2 rounded-full">
                      <User className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Signed in as</p>
                      <p className="text-sm text-gray-600">{user.email}</p>
                    </div>
                  </div>
                  <button
                    onClick={signOut}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Sign Out
                  </button>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  return <DashboardContent />;
}
