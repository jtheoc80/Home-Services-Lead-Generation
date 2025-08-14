'use client';

import { useState } from 'react';
import Card from '@/components/ui/Card';
import StatCard from '@/components/ui/StatCard';
import Badge from '@/components/ui/Badge';
import LeadScore from '@/components/ui/LeadScore';
import { 
  TestTube, 
  Plus, 
  RefreshCw, 
  Users, 
  TrendingUp, 
  Clock,
  CheckCircle,
  Mail,
  Phone,
  MapPin,
  AlertCircle
} from 'lucide-react';

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
  score?: number;
  county?: string;
  trade?: string;
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
    address: '',
    city: 'Houston',
    state: 'TX',
    zip: '',
    county: 'Harris County',
    trade: 'HVAC',
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
        body: JSON.stringify({
          ...formData,
          source: 'test'
        }),
      });
      
      const result: ApiResponse = await response.json();
      setSubmitResponse(result);
      
      if (response.ok) {
        // Clear form on success
        setFormData({
          name: '',
          email: '',
          phone: '',
          address: '',
          city: 'Houston',
          state: 'TX',
          zip: '',
          county: 'Harris County',
          trade: 'HVAC',
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
        const leads = Array.isArray(result.data) ? result.data : [result.data];
        // Add mock enhancement data for demo
        const enhancedLeads = leads.map((lead, index) => ({
          ...lead,
          score: Math.floor(Math.random() * 40) + 60, // Random score 60-100
          county: formData.county,
          trade: ['HVAC', 'Roofing', 'Electrical', 'Plumbing'][index % 4]
        }));
        setRecentLeads(enhancedLeads);
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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white">
      <div className="mx-auto max-w-7xl p-6 space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center space-x-2">
            <TestTube className="w-8 h-8 text-brand-600" />
            <h1 className="text-4xl font-bold bg-gradient-to-r from-brand-600 to-texas-600 bg-clip-text text-transparent">
              Lead Testing Laboratory
            </h1>
          </div>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Test lead creation and API integration with real-time validation and enhanced lead scoring
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            label="Test Leads Created"
            value="247"
            change={12}
            changeLabel="this week"
            icon={<Plus className="w-6 h-6" />}
            variant="success"
          />
          <StatCard
            label="API Response Time"
            value="240ms"
            change={-8}
            changeLabel="faster"
            icon={<TrendingUp className="w-6 h-6" />}
            variant="warning"
          />
          <StatCard
            label="Success Rate"
            value="98.5%"
            change={2}
            changeLabel="improvement"
            icon={<CheckCircle className="w-6 h-6" />}
            variant="success"
          />
          <StatCard
            label="Avg Score"
            value="74/100"
            icon={<TrendingUp className="w-6 h-6" />}
            variant="texas"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Lead Creation Form */}
          <Card className="p-8">
            <div className="flex items-center space-x-2 mb-6">
              <Plus className="w-5 h-5 text-brand-600" />
              <h2 className="text-2xl font-semibold text-gray-900">Create Test Lead</h2>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    placeholder="John Smith"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    placeholder="john@example.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    placeholder="(713) 555-0123"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Texas County
                  </label>
                  <select
                    name="county"
                    value={formData.county}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="Harris County">Harris County</option>
                    <option value="Fort Bend County">Fort Bend County</option>
                    <option value="Brazoria County">Brazoria County</option>
                    <option value="Galveston County">Galveston County</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Trade Type
                  </label>
                  <select
                    name="trade"
                    value={formData.trade}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  >
                    <option value="HVAC">HVAC</option>
                    <option value="Roofing">Roofing</option>
                    <option value="Electrical">Electrical</option>
                    <option value="Plumbing">Plumbing</option>
                    <option value="Remodeling">Remodeling</option>
                    <option value="Pool">Pool Installation</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ZIP Code
                  </label>
                  <input
                    type="text"
                    name="zip"
                    value={formData.zip}
                    onChange={handleInputChange}
                    className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                    placeholder="77001"
                    pattern="[0-9]{5}"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Address
                </label>
                <input
                  type="text"
                  name="address"
                  value={formData.address}
                  onChange={handleInputChange}
                  className="w-full p-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
                  placeholder="1234 Main Street, Houston, TX"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-gradient-to-r from-brand-600 to-brand-700 text-white py-3 px-6 rounded-xl font-medium hover:from-brand-700 hover:to-brand-800 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 shadow-soft"
              >
                {isSubmitting ? (
                  <div className="flex items-center justify-center space-x-2">
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Creating Lead...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-2">
                    <Plus className="w-4 h-4" />
                    <span>Create Test Lead</span>
                  </div>
                )}
              </button>
            </form>
          </Card>

          {/* Recent Leads */}
          <Card className="p-8">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Clock className="w-5 h-5 text-brand-600" />
                <h2 className="text-2xl font-semibold text-gray-900">Recent Test Leads</h2>
              </div>
              <button
                onClick={handleViewRecent}
                disabled={isLoadingRecent}
                className="inline-flex items-center px-4 py-2 bg-texas-600 text-white rounded-xl text-sm font-medium hover:bg-texas-700 disabled:opacity-50 transition-colors"
              >
                {isLoadingRecent ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Loading...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh
                  </>
                )}
              </button>
            </div>

            {recentLeads ? (
              recentLeads.length === 0 ? (
                <div className="text-center py-8">
                  <Users className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">No recent leads found.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {recentLeads.slice(0, 5).map((lead) => (
                    <div key={lead.id} className="p-4 border border-gray-200 rounded-xl hover:shadow-soft transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="space-y-2">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-semibold text-gray-900">{lead.name}</h4>
                            <Badge variant="texas" size="sm">{lead.trade}</Badge>
                          </div>
                          
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            {lead.email && (
                              <div className="flex items-center space-x-1">
                                <Mail className="w-3 h-3" />
                                <span>{lead.email}</span>
                              </div>
                            )}
                            {lead.phone && (
                              <div className="flex items-center space-x-1">
                                <Phone className="w-3 h-3" />
                                <span>{lead.phone}</span>
                              </div>
                            )}
                          </div>
                          
                          <div className="flex items-center space-x-1 text-xs text-gray-500">
                            <MapPin className="w-3 h-3" />
                            <span>{lead.county || 'Texas'}</span>
                          </div>
                        </div>

                        {lead.score && (
                          <div className="w-32">
                            <LeadScore score={lead.score} size="sm" />
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )
            ) : (
              <div className="text-center py-8">
                <Clock className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">Click "Refresh" to load recent leads</p>
              </div>
            )}
          </Card>
        </div>

        {/* API Response Display */}
        {submitResponse && (
          <Card className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              {submitResponse.error ? (
                <AlertCircle className="w-5 h-5 text-danger-600" />
              ) : (
                <CheckCircle className="w-5 h-5 text-success-600" />
              )}
              <h3 className="text-xl font-semibold text-gray-900">API Response</h3>
              {submitResponse.trace_id && (
                <Badge variant="default" size="sm">
                  ID: {submitResponse.trace_id.slice(-8)}
                </Badge>
              )}
            </div>
            
            <div className={`p-4 rounded-xl border ${
              submitResponse.error 
                ? 'bg-danger-50 border-danger-200' 
                : 'bg-success-50 border-success-200'
            }`}>
              <pre className="text-sm text-gray-800 whitespace-pre-wrap overflow-x-auto">
                {JSON.stringify(submitResponse, null, 2)}
              </pre>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

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