"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Card from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import LeadScore from "@/components/ui/LeadScore";
import MetricsCards from "@/components/MetricsCards";
import LeadCard from "@/components/LeadCard";
import TexasCountySelector from "@/components/ui/TexasCountySelector";
import DashboardHeader from "@/components/ui/DashboardHeader";
import { 
  Clock, 
  MapPin,
  Filter,
  Search,
  ChevronRight,
  AlertCircle,
  Plus
} from "lucide-react";

interface DashboardClientProps {
  leads: any[];
  initialError?: string | null;
}

/**
 * Format a date string to relative time (e.g., "2 hours ago")
 */
function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  if (diffInMinutes < 1) return 'Just now';
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
  if (diffInHours < 24) return `${diffInHours}h ago`;
  if (diffInDays < 7) return `${diffInDays}d ago`;
  if (diffInDays < 30) return `${Math.floor(diffInDays / 7)}w ago`;
  if (diffInDays < 365) return `${Math.floor(diffInDays / 30)}mo ago`;
  return `${Math.floor(diffInDays / 365)}y ago`;
}

export default function DashboardClient({ leads, initialError }: DashboardClientProps) {
  const router = useRouter();
  const [selectedCounties, setSelectedCounties] = useState<string[]>(['harris', 'dallas', 'austin', 'tarrant', 'bexar', 'elpaso']);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'score' | 'newest' | 'value'>('newest');
  const [selectedLeadTypes, setSelectedLeadTypes] = useState<string[]>([]);

  const handleExportLeads = async () => {
    try {
      const countyMap: Record<string, string> = {
        'harris': 'harris',
        'dallas': 'dallas',
        'austin': 'travis',
        'tarrant': 'tarrant',
        'bexar': 'bexar',
        'elpaso': 'el paso'
      };
      
      const params = new URLSearchParams();
      if (selectedCounties.length > 0 && selectedCounties.length < 7) {
        const mappedCounties = selectedCounties.map(c => countyMap[c.toLowerCase()] || c);
        const uniqueCounties = Array.from(new Set(mappedCounties));
        params.append('counties', uniqueCounties.join(','));
      }
      
      const response = await fetch(`/api/export?${params.toString()}`);
      
      if (!response.ok) {
        throw new Error('Export failed');
      }
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads-export-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export leads. Please try again.');
    }
  };

  // Enhanced leads with computed fields for UI compatibility
  const enhancedLeads = useMemo(() => {
    return leads?.map(lead => ({
      ...lead,
      // Use real score from database or provide a default
      score: lead.lead_score || 75,
      scoreBreakdown: {
        recency: 20,
        residential: 15,
        value: 25,
        workClass: 15,
      },
      // Use service field as tradeType
      tradeType: lead.service || 'General',
      // Use actual value from database
      permitValue: lead.value || 50000,
      // Format relative time from created_at
      lastUpdated: formatRelativeTime(lead.created_at),
      // Generate permit number from real data
      permitNumber: lead.permit_id || `TX${new Date(lead.created_at).getFullYear()}-${lead.id?.toString().slice(-6) || 'XXXXXX'}`
    })) || [];
  }, [leads]);

  const stats = useMemo(() => {
    if (!enhancedLeads) return { total: 0, newCount: 0, qualified: 0, won: 0, avgScore: 0, totalValue: 0 };
    
    const countyMap: Record<string, string> = {
      'houston': 'harris',
      'harris': 'harris',
      'dallas': 'dallas',
      'austin': 'travis',
      'tarrant': 'tarrant',
      'bexar': 'bexar',
      'elpaso': 'el paso'
    };
    
    const filteredLeads = enhancedLeads.filter(lead => 
      selectedCounties.length === 0 ||
      selectedCounties.some(county => 
        lead.county?.toLowerCase().includes(countyMap[county.toLowerCase()] || county)
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
  }, [enhancedLeads, selectedCounties]);

  const filteredLeads = useMemo(() => {
    if (!enhancedLeads) return [];
    
    const countyMap: Record<string, string> = {
      'houston': 'harris',
      'harris': 'harris',
      'dallas': 'dallas',
      'austin': 'travis',
      'tarrant': 'tarrant',
      'bexar': 'bexar',
      'elpaso': 'el paso'
    };
    
    let filtered = enhancedLeads.filter(lead => {
      const matchesCounty = selectedCounties.length === 0 || 
        selectedCounties.some(county => 
          lead.county?.toLowerCase().includes(countyMap[county.toLowerCase()] || county)
        );
      const matchesSearch = !searchTerm || 
        lead.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.service?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.tradeType?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.owner_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.contractor_name?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesLeadType = selectedLeadTypes.length === 0 ||
        selectedLeadTypes.includes(lead.lead_type || 'unknown');
      
      return matchesCounty && matchesSearch && matchesLeadType;
    });

    // Apply sorting
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'score':
          return (b.lead_score || b.score || 0) - (a.lead_score || a.score || 0);
        case 'value':
          return (b.value || b.permitValue || 0) - (a.value || a.permitValue || 0);
        case 'newest':
        default:
          return new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime();
      }
    });

    return filtered;
  }, [enhancedLeads, selectedCounties, searchTerm, sortBy, selectedLeadTypes]);

  // Show error state
  if (initialError) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
        <div className="mx-auto max-w-7xl p-6">
          <div className="flex items-center justify-center min-h-[60vh]">
            <Card className="p-8 max-w-lg text-center">
              <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Database Connection Error</h2>
              <p className="text-gray-600 mb-4">{initialError}</p>
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
      <div className="mx-auto max-w-7xl space-y-4 sm:space-y-8">
        <DashboardHeader
          title="Texas Lead Dashboard"
          subtitle="Intelligent home services lead generation across the Lone Star State"
        >
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3">
            <button
              onClick={handleExportLeads}
              className="inline-flex items-center justify-center px-4 sm:px-6 py-2 bg-green-600 text-white rounded-xl text-sm font-medium hover:bg-green-700 transition-colors"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Export CSV
            </button>
            <button
              onClick={() => router.push('/leads/new')}
              className="inline-flex items-center justify-center px-4 sm:px-6 py-2 bg-brand-600 text-white rounded-xl text-sm font-medium hover:bg-brand-700 transition-colors"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create New Lead
            </button>
          </div>
        </DashboardHeader>

        {/* Stats Grid */}
        <MetricsCards
          totalLeads={stats.total}
          totalValue={stats.totalValue}
          averageScore={stats.avgScore}
          newLeads={stats.newCount}
          loading={false}
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
              <div className="mb-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-2">
                    <Clock className="w-5 h-5 text-brand-600" />
                    <h3 className="text-xl font-semibold text-gray-900">Recent Leads</h3>
                    <span className="text-sm text-gray-500">({filteredLeads.length})</span>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {/* Sort Dropdown */}
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value as 'score' | 'newest' | 'value')}
                      className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 bg-white"
                    >
                      <option value="newest">Newest First</option>
                      <option value="score">Highest Score</option>
                      <option value="value">Highest Value</option>
                    </select>

                    {/* Search */}
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search leads..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 w-48"
                      />
                    </div>
                  </div>
                </div>

                {/* Lead Type Filters */}
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm text-gray-600 font-medium">Lead Type:</span>
                  {['owner', 'contractor', 'unknown'].map(type => {
                    const isSelected = selectedLeadTypes.includes(type);
                    return (
                      <button
                        key={type}
                        onClick={() => {
                          if (isSelected) {
                            setSelectedLeadTypes(selectedLeadTypes.filter(t => t !== type));
                          } else {
                            setSelectedLeadTypes([...selectedLeadTypes, type]);
                          }
                        }}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                          isSelected
                            ? 'bg-brand-600 text-white border-brand-600'
                            : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                        }`}
                      >
                        {type === 'owner' && '👤 '}
                        {type === 'contractor' && '🔨 '}
                        {type === 'unknown' && '❓ '}
                        {type.charAt(0).toUpperCase() + type.slice(1)}
                      </button>
                    );
                  })}
                  {selectedLeadTypes.length > 0 && (
                    <button
                      onClick={() => setSelectedLeadTypes([])}
                      className="text-xs text-gray-500 hover:text-gray-700 underline"
                    >
                      Clear filters
                    </button>
                  )}
                </div>
              </div>

              {filteredLeads.length === 0 ? (
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
        </div>
      </div>
    </div>
  );
}