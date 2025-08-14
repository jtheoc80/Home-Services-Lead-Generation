'use client';

import { useState, useMemo } from 'react';
import Card from '@/components/ui/Card';
import StatCard from '@/components/ui/StatCard';
import Badge from '@/components/ui/Badge';
import LeadScore from '@/components/ui/LeadScore';
import TexasCountySelector from '@/components/ui/TexasCountySelector';
import { 
  Search, 
  Filter, 
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
  ExternalLink
} from 'lucide-react';

interface EnhancedLead {
  id: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  service: string;
  county: string;
  status: string;
  created_at: string;
  score: number;
  scoreBreakdown: {
    recency: number;
    residential: number;
    value: number;
    workClass: number;
  };
  tradeType: string;
  permitValue: number;
  lastUpdated: string;
  permitNumber?: string;
}

const mockLeads: EnhancedLead[] = [
  {
    id: 1,
    name: "Johnson Residence Renovation",
    email: "johnson@email.com",
    phone: "(713) 555-0123",
    address: "1234 Oak Street, Houston, TX 77001",
    service: "HVAC Installation",
    county: "Harris County",
    status: "new",
    created_at: "2024-01-15T10:30:00Z",
    score: 87,
    scoreBreakdown: { recency: 23, residential: 18, value: 22, workClass: 16 },
    tradeType: "HVAC",
    permitValue: 45000,
    lastUpdated: "2 hours ago",
    permitNumber: "H2024-001234"
  },
  {
    id: 2,
    name: "Smith Home Roofing",
    email: "smith@email.com", 
    phone: "(281) 555-0456",
    address: "5678 Pine Avenue, Sugar Land, TX 77479",
    service: "Roof Replacement",
    county: "Fort Bend County",
    status: "qualified",
    created_at: "2024-01-15T08:15:00Z",
    score: 73,
    scoreBreakdown: { recency: 20, residential: 17, value: 19, workClass: 15 },
    tradeType: "Roofing",
    permitValue: 32000,
    lastUpdated: "4 hours ago",
    permitNumber: "FB2024-005678"
  },
  {
    id: 3,
    name: "Davis Electrical Upgrade",
    email: "davis@email.com",
    phone: "(832) 555-0789",
    address: "9012 Elm Drive, Pearland, TX 77584",
    service: "Electrical Panel Upgrade",
    county: "Brazoria County",
    status: "contacted",
    created_at: "2024-01-14T14:20:00Z",
    score: 65,
    scoreBreakdown: { recency: 18, residential: 16, value: 15, workClass: 14 },
    tradeType: "Electrical",
    permitValue: 18000,
    lastUpdated: "1 day ago",
    permitNumber: "BR2024-009012"
  },
  {
    id: 4,
    name: "Wilson Pool Installation",
    email: "wilson@email.com",
    phone: "(409) 555-0321",
    address: "3456 Beach Blvd, Galveston, TX 77550",
    service: "Swimming Pool",
    county: "Galveston County", 
    status: "won",
    created_at: "2024-01-13T16:45:00Z",
    score: 92,
    scoreBreakdown: { recency: 22, residential: 19, value: 25, workClass: 18 },
    tradeType: "Pool",
    permitValue: 75000,
    lastUpdated: "2 days ago",
    permitNumber: "GL2024-003456"
  },
  {
    id: 5,
    name: "Brown Kitchen Remodel",
    email: "brown@email.com",
    phone: "(713) 555-9876",
    address: "7890 Maple Street, Houston, TX 77002",
    service: "Kitchen Renovation",
    county: "Harris County",
    status: "new",
    created_at: "2024-01-15T12:00:00Z",
    score: 79,
    scoreBreakdown: { recency: 24, residential: 17, value: 20, workClass: 16 },
    tradeType: "Remodeling",
    permitValue: 38000,
    lastUpdated: "1 hour ago",
    permitNumber: "H2024-007890"
  }
];

export default function LeadsPage() {
  const [leads] = useState<EnhancedLead[]>(mockLeads);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCounties, setSelectedCounties] = useState<string[]>(['harris', 'fortbend', 'brazoria', 'galveston']);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [tradeFilter, setTradeFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('score');
  
  const filteredLeads = useMemo(() => {
    return leads
      .filter(lead => {
        const matchesSearch = !searchTerm || 
          lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.service.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.tradeType.toLowerCase().includes(searchTerm.toLowerCase()) ||
          lead.address.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesCounty = selectedCounties.length === 0 || 
          selectedCounties.some(county => 
            lead.county.toLowerCase().includes(county)
          );
        
        const matchesStatus = statusFilter === 'all' || lead.status === statusFilter;
        const matchesTrade = tradeFilter === 'all' || lead.tradeType.toLowerCase() === tradeFilter;
        
        return matchesSearch && matchesCounty && matchesStatus && matchesTrade;
      })
      .sort((a, b) => {
        switch (sortBy) {
          case 'score': return b.score - a.score;
          case 'value': return b.permitValue - a.permitValue;
          case 'date': return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
          default: return 0;
        }
      });
  }, [leads, searchTerm, selectedCounties, statusFilter, tradeFilter, sortBy]);

  const stats = useMemo(() => {
    const total = filteredLeads.length;
    const newCount = filteredLeads.filter(l => l.status === 'new').length;
    const qualified = filteredLeads.filter(l => l.status === 'qualified').length;
    const avgScore = filteredLeads.reduce((sum, l) => sum + l.score, 0) / total || 0;
    const totalValue = filteredLeads.reduce((sum, l) => sum + l.permitValue, 0);
    
    return { total, newCount, qualified, avgScore, totalValue };
  }, [filteredLeads]);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'won': return 'success';
      case 'qualified': return 'warning';
      case 'contacted': return 'texas';
      default: return 'default';
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="mx-auto max-w-7xl p-6 space-y-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between space-y-4 lg:space-y-0">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-gray-900 to-gray-600 bg-clip-text text-transparent">
              Texas Leads Management
            </h1>
            <p className="text-lg text-gray-600 mt-2">
              Advanced lead scoring and management across {selectedCounties.length} Texas counties
            </p>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            <button className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors">
              <Download className="w-4 h-4 mr-2" />
              Export CSV
            </button>
            <button className="inline-flex items-center px-6 py-2 bg-brand-600 text-white rounded-xl text-sm font-medium hover:bg-brand-700 transition-colors">
              <Target className="w-4 h-4 mr-2" />
              Add Lead
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label="Total Filtered Leads"
            value={stats.total}
            icon={<Users className="w-6 h-6" />}
            variant="default"
          />
          <StatCard
            label="New Leads"
            value={stats.newCount}
            change={12}
            changeLabel="from last week"
            icon={<TrendingUp className="w-6 h-6" />}
            variant="success"
          />
          <StatCard
            label="Avg. Lead Score"
            value={`${Math.round(stats.avgScore)}/100`}
            icon={<Target className="w-6 h-6" />}
            variant="texas"
          />
          <StatCard
            label="Total Pipeline Value"
            value={`$${(stats.totalValue / 1000).toFixed(0)}K`}
            icon={<DollarSign className="w-6 h-6" />}
            variant="warning"
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
                  <p className="text-gray-600">Try adjusting your filters or search terms.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {filteredLeads.map((lead) => (
                    <Card key={lead.id} hover className="p-6 group">
                      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between space-y-4 lg:space-y-0">
                        <div className="flex-1 space-y-3">
                          <div className="flex flex-wrap items-center gap-3">
                            <h4 className="text-lg font-semibold text-gray-900">
                              {lead.name}
                            </h4>
                            <Badge variant="texas" size="sm">
                              {lead.tradeType}
                            </Badge>
                            <Badge variant={getStatusBadgeVariant(lead.status)} size="sm">
                              {lead.status}
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
                              <span>{lead.address}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <DollarSign className="w-4 h-4" />
                              <span>${lead.permitValue.toLocaleString()} permit value</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Clock className="w-4 h-4" />
                              <span>Updated {lead.lastUpdated}</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Target className="w-4 h-4" />
                              <span>{lead.county}</span>
                            </div>
                          </div>

                          <div className="flex flex-wrap items-center gap-4">
                            <a href={`tel:${lead.phone}`} className="inline-flex items-center text-sm text-brand-600 hover:text-brand-700">
                              <Phone className="w-4 h-4 mr-1" />
                              {lead.phone}
                            </a>
                            <a href={`mailto:${lead.email}`} className="inline-flex items-center text-sm text-brand-600 hover:text-brand-700">
                              <Mail className="w-4 h-4 mr-1" />
                              {lead.email}
                            </a>
                          </div>
                        </div>

                        <div className="flex flex-col items-end space-y-4">
                          <div className="w-48">
                            <LeadScore
                              score={lead.score}
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
        </div>
      </div>
    </div>
  );
}