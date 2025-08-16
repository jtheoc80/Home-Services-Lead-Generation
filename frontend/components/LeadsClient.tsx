'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { AuthGuard, useAuth } from '@/components/AuthGuard';
import Card from '@/components/ui/Card';
import StatCard from '@/components/ui/StatCard';
import Badge from '@/components/ui/Badge';
import LeadScore from '@/components/ui/LeadScore';
import TexasCountySelector from '@/components/ui/TexasCountySelector';
import DashboardHeader from '@/components/ui/DashboardHeader';
import { 
  Search, 
  Download, 
  SortAsc,
  MapPin,
  Clock,
  Target,
  TrendingUp,
  Users,
  DollarSign,
  Phone,
  Mail,
  ExternalLink,
  AlertCircle,
  LogOut,
  User
} from 'lucide-react';

interface LeadsClientProps {
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

function LeadsPageContent({ leads, initialError }: LeadsClientProps) {
  const router = useRouter();
  const { user, signOut } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCounties, setSelectedCounties] = useState<string[]>(['harris', 'fortbend', 'brazoria', 'galveston']);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('score');
  
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
  
  const filteredLeads = useMemo(() => {
    if (!enhancedLeads) return [];
    
    return enhancedLeads
      .filter(lead => {
        const matchesSearch = !searchTerm || 
          lead.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.service?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.tradeType?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.address?.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesCounty = selectedCounties.length === 0 || 
          selectedCounties.some(county => 
            lead.county?.toLowerCase().includes(county) ||
            lead.city?.toLowerCase().includes(county)
          );
        
        const matchesStatus = statusFilter === 'all' || (lead.status?.toLowerCase() === statusFilter);
        const matchesTrade = tradeFilter === 'all' || (lead.tradeType?.toLowerCase() === tradeFilter);
        
        return matchesSearch && matchesCounty && matchesStatus && matchesTrade;
      })
      .sort((a, b) => {
        switch (sortBy) {
          case 'score': return (b.score || 0) - (a.score || 0);
          case 'value': return (b.permitValue || 0) - (a.permitValue || 0);
          case 'date': return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
          default: return 0;
        }
      });
  }, [enhancedLeads, searchTerm, selectedCounties, statusFilter, tradeFilter, sortBy]);

  const stats = useMemo(() => {
    const total = filteredLeads.length;
    const newCount = filteredLeads.filter(l => l.status?.toLowerCase() === 'new').length;
    const qualified = filteredLeads.filter(l => l.status?.toLowerCase() === 'qualified').length;
    const avgScore = filteredLeads.reduce((sum, l) => sum + (l.score || 0), 0) / total || 0;
    const totalValue = filteredLeads.reduce((sum, l) => sum + (l.permitValue || 0), 0);
    
    return { total, newCount, qualified, avgScore, totalValue };
  }, [filteredLeads]);

  const getStatusBadgeVariant = (status: string | null | undefined) => {
    switch (status?.toLowerCase()) {
      case 'won': return 'success';
      case 'qualified': return 'warning';
      case 'contacted': return 'texas';
      default: return 'default';
    }
  };

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
      <div className="mx-auto max-w-7xl p-6 space-y-8">
        <DashboardHeader
          title="Texas Leads Management"
          subtitle={`Advanced lead scoring and management across ${selectedCounties.length} Texas counties`}
        >
          <button className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
            <Download className="w-4 h-4 mr-2" />
            Export CSV
          </button>
          <button 
            className="inline-flex items-center px-6 py-2 bg-brand-600 text-white rounded-xl text-sm font-medium hover:bg-brand-700 transition-colors"
            onClick={() => router.push('/leads/new')}
          >
            <Target className="w-4 h-4 mr-2" />
            Create New Lead
          </button>
        </DashboardHeader>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label="Total Filtered Leads"
            value={stats.total}
            icon={<Users className="w-6 h-6" />}
            variant="default"
            loading={false}
          />
          <StatCard
            label="New Leads"
            value={stats.newCount}
            change={12}
            changeLabel="from last week"
            icon={<TrendingUp className="w-6 h-6" />}
            variant="success"
            loading={false}
          />
          <StatCard
            label="Avg. Lead Score"
            value={`${Math.round(stats.avgScore)}/100`}
            icon={<Target className="w-6 h-6" />}
            variant="texas"
            loading={false}
          />
          <StatCard
            label="Total Pipeline Value"
            value={`$${(stats.totalValue / 1000).toFixed(0)}K`}
            icon={<DollarSign className="w-6 h-6" />}
            variant="warning"
            loading={false}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Filters Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <TexasCountySelector
              selectedCounties={selectedCounties}
              onCountyChange={setSelectedCounties}
              showStats={true}
            />
            
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Filters</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="all">All Statuses</option>
                    <option value="new">New</option>
                    <option value="qualified">Qualified</option>
                    <option value="contacted">Contacted</option>
                    <option value="won">Won</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Trade Type</label>
                  <select
                    value={tradeFilter}
                    onChange={(e) => setTradeFilter(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="all">All Trades</option>
                    <option value="hvac">HVAC</option>
                    <option value="roofing">Roofing</option>
                    <option value="electrical">Electrical</option>
                    <option value="pool">Pool</option>
                    <option value="remodeling">Remodeling</option>
                    <option value="general">General</option>
                  </select>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="score">Lead Score</option>
                    <option value="value">Permit Value</option>
                    <option value="date">Recent Date</option>
                  </select>
                </div>
              </div>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            <Card className="p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 space-y-4 sm:space-y-0">
                <div className="flex items-center space-x-2">
                  <Clock className="w-5 h-5 text-brand-600" />
                  <h3 className="text-xl font-semibold text-gray-900">Active Leads</h3>
                  <Badge variant="default" size="sm">
                    {filteredLeads.length} results
                  </Badge>
                </div>
                
                <div className="flex items-center space-x-2">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search leads, trades, addresses..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-10 pr-4 py-2 w-64 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    />
                  </div>
                  <button className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    <SortAsc className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {filteredLeads.length === 0 ? (
                <div className="text-center py-12">
                  <Target className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No leads found</h3>
                  <p className="text-gray-600 mb-4">
                    {leads && leads.length === 0 
                      ? "No leads in the database yet."
                      : "Try adjusting your filters or search terms."
                    }
                  </p>
                  {leads && leads.length === 0 && (
                    <button 
                      onClick={() => router.push('/leads/new')}
                      className="inline-flex items-center px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors"
                    >
                      <Target className="w-4 h-4 mr-2" />
                      Create New Lead
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredLeads.map((lead) => (
                    <Card key={lead.id} hover className="p-6 group">
                      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between space-y-4 lg:space-y-0">
                        <div className="flex-1 space-y-3">
                          <div className="flex flex-wrap items-center gap-3">
                            <h4 className="text-lg font-semibold text-gray-900">
                              {lead.name || 'Unknown Lead'}
                            </h4>
                            <Badge variant="texas" size="sm">
                              {lead.tradeType || lead.service || 'General'}
                            </Badge>
                            <Badge variant={getStatusBadgeVariant(lead.status)} size="sm">
                              {lead.status || 'new'}
                            </Badge>
                            {lead.permitNumber && (
                              <Badge variant="default" size="sm">
                                {lead.permitNumber}
                              </Badge>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-gray-600">
                            <div className="flex items-center space-x-2">
                              <MapPin className="w-4 h-4" />
                              <span>{lead.address || `${lead.city || ''}, ${lead.state || 'TX'}`}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <DollarSign className="w-4 h-4" />
                              <span>${(lead.permitValue || 0).toLocaleString()} permit value</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Clock className="w-4 h-4" />
                              <span>Updated {lead.lastUpdated}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Target className="w-4 h-4" />
                              <span>{lead.county || lead.city || 'Unknown location'}</span>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-4">
                            {lead.phone && (
                              <a href={`tel:${lead.phone}`} className="inline-flex items-center text-sm text-brand-600 hover:text-brand-700">
                                <Phone className="w-4 h-4 mr-1" />
                                {lead.phone}
                              </a>
                            )}
                            {lead.email && (
                              <a href={`mailto:${lead.email}`} className="inline-flex items-center text-sm text-brand-600 hover:text-brand-700">
                                <Mail className="w-4 h-4 mr-1" />
                                {lead.email}
                              </a>
                            )}
                          </div>
                        </div>

                        <div className="flex flex-col items-end space-y-4">
                          <div className="w-48">
                            <LeadScore
                              score={lead.score || 0}
                              breakdown={lead.scoreBreakdown}
                              showDetails={false}
                              size="sm"
                            />
                          </div>
                          
                          <button className="inline-flex items-center px-4 py-2 bg-brand-600 text-white rounded-lg text-sm font-medium hover:bg-brand-700 transition-colors group-hover:shadow-soft">
                            View Details
                            <ExternalLink className="w-4 h-4 ml-2" />
                          </button>
                        </div>
                      </div>
                    </Card>
                  ))}
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

export default function LeadsClientWrapper({ leads, initialError }: LeadsClientProps) {
  return (
    <AuthGuard>
      <LeadsPageContent leads={leads} initialError={initialError} />
    </AuthGuard>
  );
}