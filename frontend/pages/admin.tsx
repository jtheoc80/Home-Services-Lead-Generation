import React, { useState, useEffect } from 'react';
import Head from 'next/head';

interface FlaggedLead {
  id: string;
  address: string;
  description?: string;
  downvote_count: number;
  days_since_first_downvote: number;
  total_feedback_count: number;
  created_at: string;
}

export default function AdminPage() {
  const [flaggedLeads, setFlaggedLeads] = useState<FlaggedLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFlaggedLeads();
  }, []);

  const fetchFlaggedLeads = async () => {
    try {
      setLoading(true);
      
      // In a real app, this would fetch from your admin API
      // Mock data for leads with ≥5 downvotes within 7 days
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockFlaggedLeads: FlaggedLead[] = [
        {
          id: '6',
          address: '999 Problem St, Houston, TX 77006',
          description: 'Suspicious lead with fake contact information',
          downvote_count: 7,
          days_since_first_downvote: 3,
          total_feedback_count: 8,
          created_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
        },
        {
          id: '7',
          address: '888 Scam Ave, Houston, TX 77007',
          description: 'Lead appears to be duplicate or low quality',
          downvote_count: 5,
          days_since_first_downvote: 6,
          total_feedback_count: 6,
          created_at: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
        }
      ];
      
      setFlaggedLeads(mockFlaggedLeads);
    } catch (err) {
      setError('Failed to load flagged leads');
      console.error('Error fetching flagged leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleIssueRefund = async (leadId: string) => {
    try {
      // In a real app, this would call your refund API
      alert(`Partial refund issued for lead ${leadId}`);
      
      // Remove from flagged list after action
      setFlaggedLeads(prev => prev.filter(lead => lead.id !== leadId));
    } catch (error) {
      console.error('Error issuing refund:', error);
      alert('Failed to issue refund');
    }
  };

  const handleSuppressSimilar = async (leadId: string) => {
    try {
      // In a real app, this would call your suppression API
      alert(`Similar leads will be suppressed for lead ${leadId}`);
      
      // Remove from flagged list after action
      setFlaggedLeads(prev => prev.filter(lead => lead.id !== leadId));
    } catch (error) {
      console.error('Error suppressing similar leads:', error);
      alert('Failed to suppress similar leads');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Head>
          <title>Admin Panel - LeadLedgerPro</title>
        </Head>
        <div className="container mx-auto px-4 py-8">
          <div className="flex justify-center items-center h-64">
            <div className="text-gray-500">Loading flagged leads...</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>Admin Panel - LeadLedgerPro</title>
        <meta name="description" content="Manage flagged leads and quality issues" />
      </Head>

      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Admin Panel
          </h1>
          <p className="text-gray-600">
            Manage leads with quality issues (≥5 downvotes within 7 days)
          </p>
        </div>

        {/* Stats Summary */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{flaggedLeads.length}</div>
              <div className="text-sm text-gray-500">Flagged Leads</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {flaggedLeads.reduce((sum, lead) => sum + lead.downvote_count, 0)}
              </div>
              <div className="text-sm text-gray-500">Total Downvotes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {flaggedLeads.filter(lead => lead.days_since_first_downvote <= 3).length}
              </div>
              <div className="text-sm text-gray-500">Recent Flags (≤3 days)</div>
            </div>
          </div>
        </div>

        {/* Flagged Leads List */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="text-red-800">{error}</div>
          </div>
        )}

        {flaggedLeads.length > 0 ? (
          <div className="space-y-4">
            {flaggedLeads.map((lead) => (
              <div key={lead.id} className="bg-white rounded-lg border border-red-200 p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {lead.address}
                    </h3>
                    <p className="text-gray-700 mb-2">{lead.description}</p>
                    <p className="text-sm text-gray-500">
                      Created: {formatDate(lead.created_at)}
                    </p>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-xl font-bold text-red-600">
                      -{lead.downvote_count}
                    </div>
                    <div className="text-xs text-gray-500">downvotes</div>
                  </div>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-4 mb-4 p-3 bg-gray-50 rounded">
                  <div className="text-center">
                    <div className="font-semibold text-red-600">{lead.downvote_count}</div>
                    <div className="text-xs text-gray-500">Downvotes</div>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-gray-700">{lead.total_feedback_count}</div>
                    <div className="text-xs text-gray-500">Total Feedback</div>
                  </div>
                  <div className="text-center">
                    <div className="font-semibold text-gray-700">{lead.days_since_first_downvote}</div>
                    <div className="text-xs text-gray-500">Days Since First</div>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex space-x-3">
                  <button
                    onClick={() => handleIssueRefund(lead.id)}
                    className="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600 transition-colors text-sm"
                  >
                    Issue Partial Refund
                  </button>
                  <button
                    onClick={() => handleSuppressSimilar(lead.id)}
                    className="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600 transition-colors text-sm"
                  >
                    Suppress Similar Leads
                  </button>
                  <button
                    onClick={() => {
                      // Navigate to lead details
                      window.open(`/dashboard/leads?lead=${lead.id}`, '_blank');
                    }}
                    className="border border-gray-300 text-gray-700 px-4 py-2 rounded hover:bg-gray-50 transition-colors text-sm"
                  >
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <div className="text-green-600 mb-4 text-lg">🎉 No flagged leads!</div>
            <div className="text-gray-500">All leads are performing well with positive feedback.</div>
          </div>
        )}

        {/* Refresh Button */}
        <div className="mt-6 text-center">
          <button
            onClick={fetchFlaggedLeads}
            className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 transition-colors"
          >
            Refresh Data
          </button>
        </div>
      </div>
    </div>
  );
}