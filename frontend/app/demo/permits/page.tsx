'use client';

import { useState, useEffect } from 'react';

// Types for permits data based on the problem statement query
interface Permit {
  id: string;
  jurisdiction: string;
  county: string;
  permit_type: string;
  value: number | null;
  status: string;
  issued_date: string;
  address: string;
}

export default function PermitsDemo() {
  const [permits, setPermits] = useState<Permit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPermits = async () => {
      try {
        setLoading(true);
        setError(null);

        // Check if Supabase is configured
        if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
          throw new Error('Supabase configuration is missing. Please set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY environment variables.');
        }

        // Dynamic import to avoid build-time issues
        const { supabase } = await import('@/lib/supabaseClient');

        // This is the exact query from the problem statement
        const { data: permits, error } = await supabase
          .from('permits')
          .select('id, jurisdiction, county, permit_type, value, status, issued_date, address')
          .order('issued_date', { ascending: false })
          .limit(50);

        if (error) {
          throw error;
        }

        setPermits(permits || []);
      } catch (err) {
        console.error('Error fetching permits:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch permits');
      } finally {
        setLoading(false);
      }
    };

    fetchPermits();
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
            Permits Demo
          </h1>
          <p className="text-gray-600">
            Testing the permits table query with the expected schema
          </p>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">
              <strong>Error:</strong> {error}
            </div>
            <div className="text-red-600 text-sm mt-2">
              Make sure the permits view has been created and the database schema is set up correctly.
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading permits data...</p>
          </div>
        )}

        {/* Content */}
        {!loading && !error && (
          <div className="bg-white rounded-lg shadow-md overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold text-gray-900">
                Recent Permits ({permits.length})
              </h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ID
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Jurisdiction
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      County
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Value
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Issued
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Address
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {permits.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                        No permits found
                      </td>
                    </tr>
                  ) : (
                    permits.map((permit, index) => (
                      <tr key={permit.id || index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {permit.id}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {permit.jurisdiction}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {permit.county}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {permit.permit_type || 'N/A'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatCurrency(permit.value)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {permit.status}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {formatDate(permit.issued_date)}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                          {permit.address}
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
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Total Permits</h3>
              <p className="text-3xl font-bold text-blue-600">{permits.length}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-900 mb-2">Avg Value</h3>
              <p className="text-3xl font-bold text-green-600">
                {permits.length > 0 
                  ? formatCurrency(
                      permits
                        .filter(p => p.value)
                        .reduce((sum, p) => sum + (p.value || 0), 0) / 
                      permits.filter(p => p.value).length
                    )
                  : 'N/A'
                }
              </p>
            </div>
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-purple-900 mb-2">Counties</h3>
              <p className="text-3xl font-bold text-purple-600">
                {new Set(permits.map(p => p.county).filter(Boolean)).size}
              </p>
            </div>
            <div className="bg-yellow-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-yellow-900 mb-2">Jurisdictions</h3>
              <p className="text-3xl font-bold text-yellow-600">
                {new Set(permits.map(p => p.jurisdiction).filter(Boolean)).size}
              </p>
            </div>
          </div>
        )}

        {/* Technical Details */}
        <div className="mt-8 bg-gray-100 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Technical Details</h3>
          <div className="text-sm text-gray-600 space-y-2">
            <p><strong>Query:</strong> <code>supabase.from(&apos;permits&apos;).select(&apos;id, jurisdiction, county, permit_type, value, status, issued_date, address&apos;)</code></p>
            <p><strong>Expected Schema:</strong> The permits view should map to the gold.permits table with proper column aliases</p>
            <p><strong>Dependencies:</strong> Requires 2025-setup.sql and create_permits_view.sql to be applied</p>
          </div>
        </div>
      </div>
    </div>
  );
}