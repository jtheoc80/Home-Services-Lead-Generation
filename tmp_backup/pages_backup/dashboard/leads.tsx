import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import LeadCard from '../../components/LeadCard';

interface Lead {
  id: number;
  jurisdiction: string;
  permit_id: string;
  address: string;
  description: string;
  work_class: string;
  category: string;
  status: string;
  issue_date: string;
  applicant: string;
  owner: string;
  value: number;
  is_residential: boolean;
  trade_tags: string[];
  budget_band: string;
  lead_score: number;
  created_at: string;
}

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('date');

  useEffect(() => {
    fetchLeads();
  }, []);

  const fetchLeads = async () => {
    try {
      // In a real app, this would fetch from your leads API
      // For now, we'll use mock data
      setLoading(true);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockLeads: Lead[] = [
        {
          id: 1,
          jurisdiction: 'City of Houston',
          permit_id: 'R2024-00123',
          address: '123 Main St, Houston, TX 77001',
          description: 'Kitchen remodel with granite countertops and new appliances',
          work_class: 'Residential',
          category: 'Alteration',
          status: 'Issued',
          issue_date: '2024-01-15',
          applicant: 'John Smith',
          owner: 'John Smith',
          value: 35000,
          is_residential: true,
          trade_tags: ['kitchen', 'remodel', 'granite'],
          budget_band: '$15-50k',
          lead_score: 85,
          created_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 2,
          jurisdiction: 'City of Houston',
          permit_id: 'R2024-00124',
          address: '456 Oak Ave, Houston, TX 77002',
          description: 'Roof replacement after storm damage',
          work_class: 'Residential',
          category: 'Repair',
          status: 'Issued',
          issue_date: '2024-01-16',
          applicant: 'ABC Roofing Inc',
          owner: 'Sarah Johnson',
          value: 15000,
          is_residential: true,
          trade_tags: ['roofing'],
          budget_band: '$5-15k',
          lead_score: 92,
          created_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: 3,
          jurisdiction: 'City of Houston',
          permit_id: 'R2024-00125',
          address: '789 Pine Dr, Houston, TX 77003',
          description: 'Full bathroom renovation with luxury fixtures',
          work_class: 'Residential',
          category: 'Alteration',
          status: 'Issued',
          issue_date: '2024-01-17',
          applicant: 'Dream Bathrooms LLC',
          owner: 'Mike Wilson',
          value: 22000,
          is_residential: true,
          trade_tags: ['bathroom', 'plumbing', 'tile'],
          budget_band: '$15-50k',
          lead_score: 78,
          created_at: new Date().toISOString(),
        },
      ];
      
      setLeads(mockLeads);
    } catch (err) {
      setError('Failed to load leads');
      console.error('Error fetching leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredAndSortedLeads = React.useMemo(() => {
    let filtered = leads;

    // Apply filters
    if (filter === 'high-value') {
      filtered = filtered.filter(lead => (lead.value || 0) >= 20000);
    } else if (filter === 'recent') {
      const twoDaysAgo = Date.now() - 2 * 24 * 60 * 60 * 1000;
      filtered = filtered.filter(lead => new Date(lead.created_at).getTime() > twoDaysAgo);
    }

    // Apply sorting
    if (sortBy === 'date') {
      filtered.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    } else if (sortBy === 'score') {
      filtered.sort((a, b) => (b.lead_score || 0) - (a.lead_score || 0));
    } else if (sortBy === 'value') {
      filtered.sort((a, b) => (b.value || 0) - (a.value || 0));
    }

    return filtered;
  }, [leads, filter, sortBy]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Head>
          <title>Leads Dashboard - LeadLedgerPro</title>
        </Head>
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-500">Loading leads...</div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Head>
          <title>Leads Dashboard - LeadLedgerPro</title>
        </Head>
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-red-600">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Leads Dashboard - LeadLedgerPro</title>
        <meta name="description" content="View and manage your home services leads" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Leads Dashboard
          </h1>
          <p className="text-gray-600">
            Manage your home services leads and provide feedback
          </p>
        </div>

        {/* Filters and Controls */}
        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center space-x-2">
              <label htmlFor="filter" className="text-sm font-medium text-gray-700">
                Filter:
              </label>
              <select
                id="filter"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
              >
                <option value="all">All Leads</option>
                <option value="recent">Recent (2 days)</option>
                <option value="high-value">High Value ($20k+)</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <label htmlFor="sort" className="text-sm font-medium text-gray-700">
                Sort by:
              </label>
              <select
                id="sort"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1 text-sm"
              >
                <option value="date">Date Added</option>
                <option value="score">Lead Score</option>
                <option value="value">Project Value</option>
              </select>
            </div>

            <div className="ml-auto text-sm text-gray-500">
              Showing {filteredAndSortedLeads.length} of {leads.length} leads
            </div>
          </div>
        </div>

        {/* Leads Grid */}
        {filteredAndSortedLeads.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAndSortedLeads.map((lead) => (
              <LeadCard key={lead.id} lead={lead} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <div className="text-gray-500 mb-4">No leads found</div>
            <button
              onClick={fetchLeads}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              Refresh
            </button>
          </div>
        )}
      </div>
    </div>
  );
}