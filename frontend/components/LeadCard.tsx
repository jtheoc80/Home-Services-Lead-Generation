
import React from 'react'

interface Lead {
  id: number
  jurisdiction: string
  permit_id: string
  address: string
  description: string
  work_class: string
  category: string
  status: string
  issue_date: string
  applicant: string
  owner: string
  value: number
  is_residential: boolean
  trade_tags: string[]
  budget_band: string
  lead_score: number
  created_at: string
}

interface FeedbackData {
  rating: 'thumbs_up' | 'thumbs_down' | null
  submitted: boolean
}

interface LeadCardProps {
  lead: Lead
  feedback?: FeedbackData
  onFeedback?: (rating: 'thumbs_up' | 'thumbs_down') => void
}

export default function LeadCard({ lead, feedback, onFeedback }: LeadCardProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getScoreColor = (score?: number) => {
    if (!score) return 'text-gray-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'issued':
        return 'text-green-700 bg-green-100'
      case 'under review':
        return 'text-yellow-700 bg-yellow-100'
      case 'rejected':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow bg-white">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {lead.address}
            </h3>
            <div className="flex items-center space-x-3">
              {/* Lead Score */}
              <span className={`px-2 py-1 rounded-full text-sm font-medium ${getScoreColor(lead.lead_score)}`}>
                Score: {lead.lead_score}
              </span>
              
              {/* Inline Feedback Buttons */}
              {onFeedback && (
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onFeedback('thumbs_up')}
                    className={`p-2 rounded-full transition-colors ${
                      feedback?.rating === 'thumbs_up'
                        ? 'bg-green-100 text-green-600'
                        : 'bg-gray-100 text-gray-400 hover:bg-green-50 hover:text-green-500'
                    }`}
                    disabled={feedback?.submitted}
                    title="Mark as good lead"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                    </svg>
                  </button>
                  
                  <button
                    onClick={() => onFeedback('thumbs_down')}
                    className={`p-2 rounded-full transition-colors ${
                      feedback?.rating === 'thumbs_down'
                        ? 'bg-red-100 text-red-600'
                        : 'bg-gray-100 text-gray-400 hover:bg-red-50 hover:text-red-500'
                    }`}
                    disabled={feedback?.submitted}
                    title="Mark as poor lead"
                  >
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" transform="rotate(180)">
                      <path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          </div>
          
          {feedback?.submitted && (
            <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium mb-2 ${
              feedback.rating === 'thumbs_up' 
                ? 'bg-green-100 text-green-800'
                : 'bg-red-100 text-red-800'
            }`}>
              Feedback submitted: {feedback.rating === 'thumbs_up' ? 'Good lead' : 'Poor lead'}
            </div>
          )}
          
          <p className="text-gray-600 mb-3">{lead.description}</p>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <div>
          <span className="font-medium text-gray-500">Permit ID:</span>
          <p className="text-gray-900">{lead.permit_id}</p>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Value:</span>
          <p className="text-gray-900">{formatCurrency(lead.value)}</p>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Issue Date:</span>
          <p className="text-gray-900">{formatDate(lead.issue_date)}</p>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Status:</span>
          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(lead.status)}`}>
            {lead.status}
          </span>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Owner:</span>
          <p className="text-gray-900">{lead.owner}</p>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Budget:</span>
          <p className="text-gray-900">{lead.budget_band}</p>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Category:</span>
          <p className="text-gray-900">{lead.category}</p>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Jurisdiction:</span>
          <p className="text-gray-900">{lead.jurisdiction}</p>
        </div>
      </div>
      
      {lead.trade_tags && lead.trade_tags.length > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <span className="font-medium text-gray-500 text-sm">Trade Tags:</span>
          <div className="flex flex-wrap gap-2 mt-2">
            {lead.trade_tags.map((tag, index) => (
              <span
                key={index}
                className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )

}