'use client';

import { useState, useEffect } from 'react';

// Types for the API responses
interface Permit {
  permit_id: string;
  city: string;
  permit_type: string | null;
  issued_at: string | null;
  valuation: number | null;
  address_full: string | null;
  contractor_name: string | null;
  status: string | null;
}

interface LeadScore {
  permit_id: string;
  city: string;
  issued_at: string | null;
  score: number;
  reasons: string[];
}

export default function TXPermitsDemo() {
  const [permits, setPermits] = useState<Permit[]>([]);
  const [leadScores, setLeadScores] = useState<LeadScore[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get API base URL from environment
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';

  // Fetch data from APIs
  const fetchData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query params
      const params = new URLSearchParams();
      if (selectedCity) {
        params.append('city', selectedCity);
      }
      
      // Fetch permits
      const permitsResponse = await fetch(`${apiBase}/api/demo/permits?${params}`);
      if (!permitsResponse.ok) {
        throw new Error(`Failed to fetch permits: ${permitsResponse.status}`);
      }
      const permitsData = await permitsResponse.json();
      setPermits(permitsData);
      
      // Fetch lead scores
      const scoresResponse = await fetch(`${apiBase}/api/leads/scores?${params}`);
      if (!scoresResponse.ok) {
        throw new Error(`Failed to fetch scores: ${scoresResponse.status}`);
      }
      const scoresData = await scoresResponse.json();
      setLeadScores(scoresData);
      
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  // Fetch data on component mount and when city filter changes
  useEffect(() => {
    fetchData();
  }, [selectedCity]);

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
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid Date';
    }
  };

  // Get score color class
  const getScoreColorClass = (score: number) => {
    if (score >= 80) return 'text-green-600 font-bold';
    if (score >= 60) return 'text-yellow-600 font-semibold';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Texas Permits Demo
          </h1>
          <p className="text-gray-600">
            Live permit data from Dallas, Austin, and Arlington with AI-powered lead scoring
          </p>
        </div>

        {/* City Filter */}
        <div className="mb-6">
          <label htmlFor="city-select" className="block text-sm font-medium text-gray-700 mb-2">
            Filter by City:
          </label>
          <select
            id="city-select"
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="border border-gray-300 rounded-md px-3 py-2 bg-white shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="">All Cities</option>
            <option value="Dallas">Dallas</option>
            <option value="Austin">Austin</option>
            <option value="Arlington">Arlington</option>
          </select>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="text-red-800">
              <strong>Error:</strong> {error}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">Loading permit data...</p>
          </div>
        )}

        {/* Content */}
        {!loading && !error && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            
            {/* Recent Permits Table */}
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
                        City
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Permit ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Issued
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Valuation
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {permits.length === 0 ? (
                      <tr>
                        <td colSpan={5} className="px-6 py-4 text-center text-gray-500">
                          No permits found
                        </td>
                      </tr>
                    ) : (
                      permits.slice(0, 20).map((permit, index) => (
                        <tr key={`${permit.permit_id}-${index}`} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {permit.city}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {permit.permit_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {permit.permit_type || 'N/A'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(permit.issued_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatCurrency(permit.valuation)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Lead Scores Table */}
            <div className="bg-white rounded-lg shadow-md overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200">
                <h2 className="text-xl font-semibold text-gray-900">
                  Lead Scores ({leadScores.length})
                </h2>
              </div>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        City
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Permit ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Issued
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Score
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {leadScores.length === 0 ? (
                      <tr>
                        <td colSpan={4} className="px-6 py-4 text-center text-gray-500">
                          No scored leads found
                        </td>
                      </tr>
                    ) : (
                      leadScores.slice(0, 20).map((score, index) => (
                        <tr key={`${score.permit_id}-${index}`} className="hover:bg-gray-50">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {score.city}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {score.permit_id}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(score.issued_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={getScoreColorClass(score.score)}>
                              {score.score}/100
                            </span>
                            {score.reasons.length > 0 && (
                              <div className="text-xs text-gray-400 mt-1">
                                {score.reasons[0]}
                              </div>
                            )}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Stats Summary */}
        {!loading && !error && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Total Permits</h3>
              <p className="text-3xl font-bold text-blue-600">{permits.length}</p>
            </div>
            <div className="bg-green-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-green-900 mb-2">Scored Leads</h3>
              <p className="text-3xl font-bold text-green-600">{leadScores.length}</p>
            </div>
            <div className="bg-purple-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-purple-900 mb-2">Avg Score</h3>
              <p className="text-3xl font-bold text-purple-600">
                {leadScores.length > 0 
                  ? Math.round(leadScores.reduce((sum, s) => sum + s.score, 0) / leadScores.length)
                  : 0
                }
              </p>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm">
          <p>
            Data refreshed automatically from Dallas, Austin, and Arlington permit APIs.
            Lead scores computed using scoring algorithm v0.
          </p>
        </div>
      </div>
    </div>
  );
}