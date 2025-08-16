"use client";

import { useMemo, useState } from "react";
import { useEnhancedLeads } from "@/hooks/useLeads";
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
  ChevronRight,
  AlertCircle
} from "lucide-react";

export default function Dashboard() {
  const { leads, error, loading } = useEnhancedLeads();
  const [selectedCounties, setSelectedCounties] = useState<string[]>(['harris', 'fortbend']);
  const [searchTerm, setSearchTerm] = useState('');

  const stats = useMemo(() => {
    if (!leads) return { total: 0, newCount: 0, qualified: 0, won: 0, avgScore: 0, totalValue: 0 };
    
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
            <Card className="p-8 max-w-md text-center">
              <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Database Connection Error</h2>
              <p className="text-gray-600 mb-4">{error}</p>
              <p className="text-sm text-gray-500">
                Please check your Supabase configuration in the .env.local file.
              </p>
            </Card>
          </div>
        </div>
      </div>
    );
  }

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
                  {filteredLeads.slice(0, 6).map((lead) => (
                    <div
                      key={lead.id}
                      className="p-4 border border-gray-200 rounded-xl hover:shadow-soft-lg transition-all duration-300 group cursor-pointer"
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0 space-y-2">
                          <div className="flex items-center space-x-3">
                            <h4 className="font-semibold text-gray-900 truncate">
                              {lead.name || 'Unknown Lead'}
                            </h4>
                            <Badge variant="texas" size="sm">
                              {lead.tradeType || lead.service || 'General'}
                            </Badge>
                            <Badge 
                              variant={
                                lead.status === 'won' ? 'success' :
                                lead.status === 'qualified' ? 'warning' :
                                lead.status === 'contacted' ? 'texas' : 'default'
                              }
                              size="sm"
                            >
                              {lead.status || 'new'}
                            </Badge>
                          </div>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span className="flex items-center space-x-1">
                              <MapPin className="w-4 h-4" />
                              <span>{lead.county || lead.city || 'Unknown location'}</span>
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
                      onClick={() => (window.location.href = "/leads")}
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
