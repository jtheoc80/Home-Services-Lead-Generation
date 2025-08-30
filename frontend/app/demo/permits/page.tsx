'use client';

import { useState, useEffect } from 'react';

import type { LeadForPermitsView } from '@/types';

export default function PermitsDemo() {
  const [leads, setLeads] = useState<LeadForPermitsView[]>([]);

import { getLeads, type Lead } from '@/lib/actions/leads';

export default function PermitsDemo() {
  const [leads, setLeads] = useState<Lead[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLeads = async () => {
      try {
        setLoading(true);
        setError(null);


        // Check if Supabase is configured
        if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
          throw new Error('Supabase configuration is missing. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.');
        }

        // Dynamic import to avoid build-time issues
        const { supabase } = await import('@/lib/supabaseClient');
        
        if (!supabase) {
          throw new Error('Failed to initialize Supabase client');
        }

        // Use the leads server action instead of direct Supabase query
        const { data: leadsData, error } = await getLeads();

        if (error) {
          throw new Error(error);
        }

        setLeads(leadsData || []);
      } catch (err) {
        console.error('Error fetching leads:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch leads');
      } finally {
        setLoading(false);
      }
    };

    fetchLeads();
  }, []);

  // Format currency
  const formatCurrency = (value: number | null) => {
    if (!value) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(value);
  };

  // Format date
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid Date';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">

            Permits Demo (Now Using Leads)
          </h1>
          <p className="text-gray-600">
            Testing the leads table query with fields mapped to permits structure

            Leads Demo
          </h1>
          <p className="text-gray-600">
            Testing the leads table query with proper TypeScript types

          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">
              <strong>Error:</strong> {error}
            </div>
            <div className="text-red-600 text-sm mt-2">

              Make sure the leads table has been created and the database schema is set up correctly.

              Make sure the leads table exists and the database schema is set up correctly.

            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading leads data...</p>
          </div>
        )}

        {/* Content */}
        {!loading && !error && (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Recent Leads ({leads.length})
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">

                      City

                      Phone

                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Email
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">

                      Service Type

                      County

                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">

                      Created

                      Score

                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {leads.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                        No leads found
                      </td>
                    </tr>
                  ) : (
                    leads.map((lead, index) => (
                      <tr key={lead.id || index} className="hover:bg-gray-50">

                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {lead.city || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.county || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.service || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatCurrency(lead.value)}

                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {lead.name || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.phone || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.email || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.county || 'N/A'}

                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.status || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">

                          {formatDate(lead.created_at)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                          {lead.address || 'N/A'}

                          {lead.source || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {lead.lead_score || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(lead.created_at || '')}

                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Stats Summary */}
        {!loading && !error && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Total Leads</h3>
              <p className="text-3xl font-bold text-blue-600">{leads.length}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-900 mb-2">Avg Score</h3>
              <p className="text-3xl font-bold text-green-600">

                {leads.length > 0 
                  ? formatCurrency(
                      leads
                        .filter(l => l.value)
                        .reduce((sum, l) => sum + (l.value || 0), 0) / 
                      leads.filter(l => l.value).length
                    )
                  : 'N/A'
                }

                {(() => {
                  if (leads.length === 0) return 'N/A';
                  const scoredLeads = leads.filter((lead: Lead) => lead.lead_score);
                  if (scoredLeads.length === 0) return 'N/A';
                  const avg = scoredLeads.reduce((sum: number, lead: Lead) => sum + (lead.lead_score || 0), 0) / scoredLeads.length;
                  return Number.isNaN(avg) ? 'N/A' : Math.round(avg);
                })()}

              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-purple-900 mb-2">Counties</h3>
              <p className="text-3xl font-bold text-purple-600">

                {new Set(leads.map(l => l.county).filter(Boolean)).size}
              </p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">Cities</h3>
              <p className="text-3xl font-bold text-yellow-600">
                {new Set(leads.map(l => l.city).filter(Boolean)).size}

                {new Set(leads.map((lead: Lead) => lead.county).filter(Boolean)).size}
              </p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">Sources</h3>
              <p className="text-3xl font-bold text-yellow-600">
                {new Set(leads.map((lead: Lead) => lead.source).filter(Boolean)).size}

              </p>
            </div>
          </div>
        )}

        {/* Technical Details */}
        <div className="mt-8 bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Details</h3>
          <div className="text-sm text-gray-600 space-y-2">

            <p><strong>Query:</strong> <code>supabase.from(&apos;leads&apos;).select(&apos;id, city, county, service, value, status, created_at, address&apos;)</code></p>
            <p><strong>Field Mapping:</strong> city→jurisdiction, service→permit_type, created_at→issued_date</p>
            <p><strong>Dependencies:</strong> Requires leads table to be set up with proper schema</p>

            <p><strong>Query:</strong> <code>supabase.from(&apos;leads&apos;).select(&apos;id, name, phone, email, address, city, state, county, status, source, lead_score, value, created_at&apos;)</code></p>
            <p><strong>TypeScript Types:</strong> Using proper Lead interface from types/supabase.ts for full type safety</p>
            <p><strong>Dependencies:</strong> Requires leads table and RLS policies to be configured</p>

          </div>
        </div>
      </div>
    </div>
  );
}