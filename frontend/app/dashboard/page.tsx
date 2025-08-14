"use client";

import { useEffect, useMemo, useState } from "react";
import { Lead } from "@/types/supabase";
import StatCard from "@/components/ui/StatCard";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import LeadScore from "@/components/ui/LeadScore";
import TexasCountySelector from "@/components/ui/TexasCountySelector";
import { 
  Users, 
  TrendingUp, 
  Target, 
  Trophy, 
  Clock, 
  MapPin,
  Filter,
  Search,
  ChevronRight
} from "lucide-react";

interface EnhancedLead extends Lead {
  score?: number;
  scoreBreakdown?: {
    recency: number;
    residential: number;
    value: number;
    workClass: number;
  };
  tradeType?: string;
  permitValue?: number;
  lastUpdated?: string;
}

export default function Dashboard() {
  const [leads, setLeads] = useState<EnhancedLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [selectedCounties, setSelectedCounties] = useState<string[]>(['harris', 'fortbend']);
  const [searchTerm, setSearchTerm] = useState('');

  // Mock enhanced lead data for demo
  useEffect(() => {
    const mockEnhancedLeads: EnhancedLead[] = [
      {
        id: 1,
        name: "Johnson Residence Renovation",
        email: "johnson@email.com",
        phone: "(713) 555-0123",
        service: "HVAC Installation",
        county: "Harris County",
        status: "new",
        created_at: "2024-01-15T10:30:00Z",
        score: 87,
        scoreBreakdown: { recency: 23, residential: 18, value: 22, workClass: 16 },
        tradeType: "HVAC",
        permitValue: 45000,
        lastUpdated: "2 hours ago"
      },
      {
        id: 2,
        name: "Smith Home Roofing",
        email: "smith@email.com", 
        phone: "(281) 555-0456",
        service: "Roof Replacement",
        county: "Fort Bend County",
        status: "qualified",
        created_at: "2024-01-15T08:15:00Z",
        score: 73,
        scoreBreakdown: { recency: 20, residential: 17, value: 19, workClass: 15 },
        tradeType: "Roofing",
        permitValue: 32000,
        lastUpdated: "4 hours ago"
      },
      {
        id: 3,
        name: "Davis Electrical Upgrade",
        email: "davis@email.com",
        phone: "(832) 555-0789",
        service: "Electrical Panel Upgrade",
        county: "Brazoria County",
        status: "contacted",
        created_at: "2024-01-14T14:20:00Z",
        score: 65,
        scoreBreakdown: { recency: 18, residential: 16, value: 15, workClass: 14 },
        tradeType: "Electrical",
        permitValue: 18000,
        lastUpdated: "1 day ago"
      },
      {
        id: 4,
        name: "Wilson Pool Installation",
        email: "wilson@email.com",
        phone: "(409) 555-0321",
        service: "Swimming Pool",
        county: "Galveston County", 
        status: "won",
        created_at: "2024-01-13T16:45:00Z",
        score: 92,
        scoreBreakdown: { recency: 22, residential: 19, value: 25, workClass: 18 },
        tradeType: "Pool",
        permitValue: 75000,
        lastUpdated: "2 days ago"
      }
    ];

    (async () => {
      // Simulate async data loading with a Promise-based delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      setLeads(mockEnhancedLeads);
      setLoading(false);
    })();
  }, []);

  const stats = useMemo(() => {
    const filteredLeads = leads.filter(lead => 
      selectedCounties.some(county => 
        lead.county?.toLowerCase().includes(county)
      )
    );
    
    const total = filteredLeads.length;
    const newCount = filteredLeads.filter((l) => (l.status ?? "").toLowerCase() === "new").length;
    const qualified = filteredLeads.filter((l) => (l.status ?? "").toLowerCase() === "qualified").length;
    const won = filteredLeads.filter((l) => (l.status ?? "").toLowerCase() === "won").length;
    const avgScore = filteredLeads.reduce((sum, l) => sum + (l.score || 0), 0) / total || 0;
    const totalValue = filteredLeads.reduce((sum, l) => sum + (l.permitValue || 0), 0);
    
    return { total, newCount, qualified, won, avgScore, totalValue };
  }, [leads, selectedCounties]);

  const filteredLeads = useMemo(() => {
    return leads.filter(lead => {
      const matchesCounty = selectedCounties.some(county => 
        lead.county?.toLowerCase().includes(county)
      );
      const matchesSearch = !searchTerm || 
        lead.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.service?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.tradeType?.toLowerCase().includes(searchTerm.toLowerCase());
      
      return matchesCounty && matchesSearch;
    });
  }, [leads, selectedCounties, searchTerm]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="mx-auto max-w-7xl p-6 space-y-8">
        {/* Header */}
        <div className="space-y-2">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
            Texas Lead Dashboard
          </h1>
          <p className="text-lg text-gray-600">
            Intelligent home services lead generation across the Lone Star State
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label="Total Leads"
            value={loading ? "—" : stats.total}
            change={12}
            changeLabel="from last week"
            icon={<Users className="w-6 h-6" />}
            variant="default"
            loading={loading}
          />
          <StatCard
            label="New Leads"
            value={loading ? "—" : stats.newCount}
            change={8}
            changeLabel="today"
            icon={<TrendingUp className="w-6 h-6" />}
            variant="success"
            loading={loading}
          />
          <StatCard
            label="Avg. Lead Score"
            value={loading ? "—" : `${Math.round(stats.avgScore)}/100`}
            change={5}
            changeLabel="improvement"
            icon={<Target className="w-6 h-6" />}
            variant="texas"
            loading={loading}
          />
          <StatCard
            label="Total Value"
            value={loading ? "—" : `$${(stats.totalValue / 1000).toFixed(0)}K`}
            change={15}
            changeLabel="this month"
            icon={<Trophy className="w-6 h-6" />}
            variant="warning"
            loading={loading}
          />
        </div>

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

              {err ? (
                <div className="p-6 text-center text-danger-600 bg-danger-50 rounded-lg">
                  Error: {err}
                </div>
              ) : loading ? (
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
                  <p>Try adjusting your county selection or search terms.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredLeads.slice(0, 6).map((lead) => (
                    <div
                      key={lead.id}
                      className="p-4 border border-gray-200 rounded-xl hover:shadow-soft-lg transition-all duration-300 group cursor-pointer"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0 space-y-2">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-semibold text-gray-900 truncate">
                              {lead.name}
                            </h4>
                            <Badge variant="texas" size="sm">
                              {lead.tradeType}
                            </Badge>
                            <Badge 
                              variant={
                                lead.status === 'won' ? 'success' :
                                lead.status === 'qualified' ? 'warning' :
                                lead.status === 'contacted' ? 'texas' : 'default'
                              }
                              size="sm"
                            >
                              {lead.status}
                            </Badge>
                          </div>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-4 h-4" />
                              <span>{lead.county}</span>
                            </span>
                            <span>${(lead.permitValue || 0).toLocaleString()}</span>
                            <span>{lead.lastUpdated}</span>
                          </div>
                        </div>

                        <div className="flex items-center space-x-4">
                          <div className="w-32">
                            <LeadScore
                              score={lead.score || 0}
                              size="sm"
                              showDetails={false}
                            />
                          </div>
                          <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-brand-600 transition-colors" />
                        </div>
                      </div>
                    </div>
                  ))}

                  <div className="mt-6 text-center">
                    <button
                      onClick={() => (location.href = "/leads")}
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
        </div>
      </div>
    </div>
  );
}
