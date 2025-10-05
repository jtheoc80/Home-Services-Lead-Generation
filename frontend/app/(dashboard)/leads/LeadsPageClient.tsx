'use client';

import { useState, useMemo } from 'react';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import LeadScore from '@/components/ui/LeadScore';
import { FileText, Search, Filter, Download, TrendingUp, MapPin, AlertCircle } from 'lucide-react';

interface Lead {
  id: number;
  name: string;
  trade: string;
  county: string;
  status: string;
  lead_score: number;
  created_at: string;
  address?: string;
  zipcode?: string;
  value?: number;
  external_permit_id?: string;
}

interface LeadsPageClientProps {
  leads: Lead[];
  error?: string;
}

export default function LeadsPageClient({ leads, error }: LeadsPageClientProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [scoreFilter, setScoreFilter] = useState<string>('all');

  const filteredLeads = useMemo(() => {
    return leads.filter(lead => {
      const matchesSearch = !searchTerm || 
        lead.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.trade?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.address?.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesStatus = statusFilter === 'all' || lead.status?.toLowerCase() === statusFilter.toLowerCase();
      
      const matchesScore = scoreFilter === 'all' || 
        (scoreFilter === 'hot' && lead.lead_score >= 90) ||
        (scoreFilter === 'warm' && lead.lead_score >= 60 && lead.lead_score < 90) ||
        (scoreFilter === 'cold' && lead.lead_score < 60);

      return matchesSearch && matchesStatus && matchesScore;
    });
  }, [leads, searchTerm, statusFilter, scoreFilter]);

  const stats = useMemo(() => {
    const total = filteredLeads.length;
    const hot = filteredLeads.filter(l => l.lead_score >= 90).length;
    const warm = filteredLeads.filter(l => l.lead_score >= 60 && l.lead_score < 90).length;
    const cold = filteredLeads.filter(l => l.lead_score < 60).length;
    const avgScore = total > 0 ? filteredLeads.reduce((sum, l) => sum + l.lead_score, 0) / total : 0;

    return { total, hot, warm, cold, avgScore };
  }, [filteredLeads]);

  if (error) {
    return (
      <div className="p-6">
        <Card className="p-8 text-center">
          <AlertCircle className="w-12 h-12 mx-auto text-red-500 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Leads</h2>
          <p className="text-gray-600">{error}</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 bg-gradient-to-br from-gray-50 to-white min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">All Leads</h1>
          <p className="text-slate-600 mt-1">Manage and track your lead pipeline</p>
        </div>
        <button className="inline-flex items-center px-6 py-3 bg-navy-600 text-white rounded-xl font-medium hover:bg-navy-700 transition-all duration-200 shadow-soft">
          <Download className="w-4 h-4 mr-2" />
          Export All
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="p-4 border-l-4 border-navy-600">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 font-medium">Total Leads</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.total}</p>
            </div>
            <div className="p-3 bg-navy-50 rounded-xl">
              <FileText className="w-6 h-6 text-navy-600" />
            </div>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-red-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 font-medium">Hot Leads</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.hot}</p>
            </div>
            <div className="p-3 bg-red-50 rounded-xl">
              <TrendingUp className="w-6 h-6 text-red-500" />
            </div>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 font-medium">Warm Leads</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.warm}</p>
            </div>
            <div className="p-3 bg-orange-50 rounded-xl">
              <TrendingUp className="w-6 h-6 text-orange-500" />
            </div>
          </div>
        </Card>

        <Card className="p-4 border-l-4 border-slate-400">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 font-medium">Avg Score</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">{stats.avgScore.toFixed(0)}</p>
            </div>
            <div className="p-3 bg-slate-100 rounded-xl">
              <TrendingUp className="w-6 h-6 text-slate-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex-1 min-w-[250px]">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Search leads by name, trade, or address..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-navy-500 focus:border-navy-500 transition-all"
              />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
            >
              <option value="all">All Status</option>
              <option value="new">New</option>
              <option value="qualified">Qualified</option>
              <option value="won">Won</option>
            </select>

            <select
              value={scoreFilter}
              onChange={(e) => setScoreFilter(e.target.value)}
              className="px-4 py-2 border border-slate-300 rounded-xl text-sm focus:ring-2 focus:ring-navy-500 focus:border-navy-500"
            >
              <option value="all">All Scores</option>
              <option value="hot">Hot (90+)</option>
              <option value="warm">Warm (60-89)</option>
              <option value="cold">Cold (&lt;60)</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Leads Table */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-navy-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-navy-700 uppercase tracking-wider">Lead</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-navy-700 uppercase tracking-wider">Trade</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-navy-700 uppercase tracking-wider">Location</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-navy-700 uppercase tracking-wider">Score</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-navy-700 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-navy-700 uppercase tracking-wider">Value</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-navy-700 uppercase tracking-wider">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {filteredLeads.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                    <MapPin className="w-12 h-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-lg font-medium">No leads found</p>
                    <p className="text-sm mt-1">Try adjusting your filters or search terms</p>
                  </td>
                </tr>
              ) : (
                filteredLeads.map((lead) => (
                  <tr key={lead.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-gray-900">{lead.name}</div>
                        {lead.external_permit_id && (
                          <div className="text-xs text-slate-500 mt-1">Permit #{lead.external_permit_id}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <Badge variant="texas" size="sm">{lead.trade}</Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm">
                        <div className="text-gray-900">{lead.county}</div>
                        {lead.zipcode && <div className="text-slate-500">{lead.zipcode}</div>}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <LeadScore score={lead.lead_score} size="sm" />
                    </td>
                    <td className="px-6 py-4">
                      <Badge 
                        variant={
                          lead.status?.toLowerCase() === 'won' ? 'success' : 
                          lead.status?.toLowerCase() === 'qualified' ? 'warning' : 
                          'default'
                        }
                        size="sm"
                      >
                        {lead.status}
                      </Badge>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">
                        {lead.value ? `$${lead.value.toLocaleString()}` : '—'}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm text-slate-600">
                      {new Date(lead.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
