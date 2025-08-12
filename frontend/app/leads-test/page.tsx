'use client';

import { useState } from 'react';

interface Lead {
  id: string;
  name: string | null;
  email: string | null;
  phone: string | null;
  source: string;
  created_at: string;
  address: string | null;
  city: string | null;
  state: string | null;
  zip: string | null;
}

interface ApiResponse {
  data?: Lead | Lead[];
  count?: number;
  error?: string;
  trace_id: string;
}

export default function LeadsTestPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    source: 'test'
  });
  const [submitResponse, setSubmitResponse] = useState<ApiResponse | null>(null);
  const [recentLeads, setRecentLeads] = useState<Lead[] | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingRecent, setIsLoadingRecent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitResponse(null);

    try {
      const response = await fetch('/api/leads', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const result: ApiResponse = await response.json();
      setSubmitResponse(result);

      // Clear form if successful
      if (response.ok) {
        setFormData({
          name: '',
          email: '',
          phone: '',
          source: 'test'
        });
      }
    } catch (error) {
      setSubmitResponse({
        error: 'Network error occurred',
        trace_id: 'client-error-' + Date.now()
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewRecent = async () => {
    setIsLoadingRecent(true);
    setRecentLeads(null);

    try {
      const response = await fetch('/api/leads/recent');
      const result: ApiResponse = await response.json();
      
      if (response.ok && result.data) {
        setRecentLeads(Array.isArray(result.data) ? result.data : [result.data]);
      } else {
        console.error('Error fetching recent leads:', result.error);
        setRecentLeads([]);
      }
    } catch (error) {
      console.error('Network error:', error);
      setRecentLeads([]);
    } finally {
      setIsLoadingRecent(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <h1 className="text-2xl font-bold text-yellow-800 mb-2">🧪 Leads Test Page</h1>
        <p className="text-yellow-700">
          This is a hidden test page for submitting and verifying lead data.
        </p>
      </div>

      {/* Lead Submission Form */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Submit Test Lead</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                Name
              </label>
              <input
                type="text"
                id="name"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter full name"
              />
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter email address"
              />
            </div>

            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter phone number"
              />
            </div>

            <div>
              <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-1">
                Source
              </label>
              <select
                id="source"
                name="source"
                value={formData.source}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="test">Test</option>
                <option value="web">Web</option>
                <option value="api">API</option>
                <option value="manual">Manual</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Lead'}
          </button>
        </form>
      </div>

      {/* Response Display */}
      {submitResponse && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold mb-4">API Response</h2>
          <div className="bg-gray-50 p-4 rounded-md">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto">
              {JSON.stringify(submitResponse, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* View Recent Leads */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">Recent Leads</h2>
          <button
            onClick={handleViewRecent}
            disabled={isLoadingRecent}
            className="bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 disabled:bg-green-300 disabled:cursor-not-allowed"
          >
            {isLoadingRecent ? 'Loading...' : 'View Recent'}
          </button>
        </div>

        {recentLeads && (
          <div className="space-y-4">
            {recentLeads.length === 0 ? (
              <p className="text-gray-500">No recent leads found.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full border border-gray-300">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Name</th>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Email</th>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Phone</th>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Source</th>
                      <th className="px-4 py-2 text-left text-sm font-medium text-gray-700 border-b">Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentLeads.map((lead, index) => (
                      <tr key={lead.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-4 py-2 text-sm text-gray-900 border-b">{lead.name || '-'}</td>
                        <td className="px-4 py-2 text-sm text-gray-900 border-b">{lead.email || '-'}</td>
                        <td className="px-4 py-2 text-sm text-gray-900 border-b">{lead.phone || '-'}</td>
                        <td className="px-4 py-2 text-sm text-gray-900 border-b">{lead.source}</td>
                        <td className="px-4 py-2 text-sm text-gray-900 border-b">
                          {new Date(lead.created_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}