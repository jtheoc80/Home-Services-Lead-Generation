'use client';

import { useEffect, useState } from 'react';
import EmptyState from '@/components/EmptyState';
import { Lead } from '../../../types/supabase';

interface LeadsResponse {
  data: Lead[];
  count: number;
  trace_id: string;
}

export default function Dashboard() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastRefreshedMinutes, setLastRefreshedMinutes] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const fetchLeads = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/leads/recent');
      
      if (!response.ok) {
        throw new Error(`Failed to fetch leads: ${response.statusText}`);
      }
      
      const data: LeadsResponse = await response.json();
      setLeads(data.data || []);
      setLastRefreshedMinutes(0); // Just refreshed
      setError(null);
    } catch (error) {
      console.error('Error fetching leads:', error);
      setError(error instanceof Error ? error.message : 'Unknown error');
      setLeads([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, []);

  // Update refresh time every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setLastRefreshedMinutes(prev => prev + 1);
    }, 60000); // Update every minute

    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return (
      <div className="p-6 space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-10 rounded-md bg-gray-100 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!leads?.length) {
    return (
      <EmptyState
        title="No leads yet"
        subtitle="Connect your region and run your first hourly sync to see live permits."
        ctaLabel="Connect region"
        ctaHref="/settings/regions"
      />
    );
  }

  return (
    <div className="p-6">
      <div className="mb-3 text-sm text-gray-500">
        Last refreshed: {lastRefreshedMinutes} min ago
      </div>
      
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
          {error}
        </div>
      )}

      {/* Simple table for leads */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Phone
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Location
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {lead.name || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {lead.email || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {lead.phone || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {lead.city && lead.state ? `${lead.city}, ${lead.state}` : lead.address || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(lead.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}