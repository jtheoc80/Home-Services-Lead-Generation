import React from 'react';
import LeadFeedbackButtons from './LeadFeedbackButtons';

interface Lead {
  id: string;
  address: string;
  description?: string;
  value?: number;
  trade_tags?: string[];
  created_at: string;
  lead_score?: number;
  initialVote?: 'up' | 'down';
}

interface LeadCardProps {
  lead: Lead;
}

export default function LeadCard({ lead }: LeadCardProps) {
  const formatValue = (value?: number) => {
    if (!value) return 'N/A';
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

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md transition-shadow">
      {/* Header with address and date */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-1">
            {lead.address}
          </h3>
          <p className="text-sm text-gray-500">
            Posted {formatDate(lead.created_at)}
          </p>
        </div>
        {lead.lead_score && (
          <div className="text-right">
            <div className={`text-lg font-bold ${getScoreColor(lead.lead_score)}`}>
              {lead.lead_score}
            </div>
            <div className="text-xs text-gray-500">Score</div>
          </div>
        )}
      </div>

      {/* Description */}
      {lead.description && (
        <p className="text-gray-700 mb-3 text-sm line-clamp-2">
          {lead.description}
        </p>
      )}

      {/* Tags and Value */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex flex-wrap gap-1">
          {lead.trade_tags?.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full"
            >
              {tag}
            </span>
          ))}
          {lead.trade_tags && lead.trade_tags.length > 3 && (
            <span className="text-xs text-gray-500">
              +{lead.trade_tags.length - 3} more
            </span>
          )}
        </div>
        
        {lead.value && (
          <div className="text-sm font-semibold text-gray-900">
            {formatValue(lead.value)}
          </div>
        )}
      </div>

      {/* Footer with actions */}
      <div className="flex justify-between items-center pt-3 border-t border-gray-100">
        <div className="flex space-x-2">
          <button className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600 transition-colors">
            View Details
          </button>
          <button className="text-sm border border-gray-300 text-gray-700 px-3 py-1 rounded hover:bg-gray-50 transition-colors">
            Contact
          </button>
        </div>
        
        {/* Feedback buttons */}
        <LeadFeedbackButtons 
          leadId={lead.id} 
          initialVote={lead.initialVote}
        />
      </div>
    </div>
  );
}