import React from 'react';
import { MapPin, Building, Phone, Mail, User, HardHat } from 'lucide-react';
import { Lead } from '../types/leads';

interface FeedbackData {
  rating: 'thumbs_up' | 'thumbs_down' | null;
  submitted: boolean;
}

interface LeadCardProps {
  lead: Lead;
  feedback?: FeedbackData;
  onFeedback?: (rating: 'thumbs_up' | 'thumbs_down') => void;
  showFeedback?: boolean;
  compact?: boolean;
}

export default function LeadCard({ 
  lead, 
  feedback, 
  onFeedback, 
  showFeedback = false,
  compact = false 
}: LeadCardProps) {
  const formatCurrency = (value?: number | null) => {
    if (!value) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatDate = (dateString?: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatRelativeTime = (dateString?: string | null) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    const diffInDays = Math.floor(diffInHours / 24);
    if (diffInDays < 7) return `${diffInDays}d ago`;
    return formatDate(dateString);
  };

  const getScoreColor = (score?: number | null) => {
    if (!score) return 'text-gray-700 bg-gray-100';
    if (score >= 80) return 'text-green-700 bg-green-100';
    if (score >= 60) return 'text-yellow-700 bg-yellow-100';
    return 'text-red-700 bg-red-100';
  };

  const getStatusColor = (status?: string | null) => {
    if (!status) return 'text-gray-700 bg-gray-100';
    switch (status.toLowerCase()) {
      case 'new':
        return 'text-blue-700 bg-blue-100';
      case 'qualified':
        return 'text-green-700 bg-green-100';
      case 'contacted':
        return 'text-yellow-700 bg-yellow-100';
      case 'won':
        return 'text-green-700 bg-green-100';
      case 'lost':
        return 'text-red-700 bg-red-100';
      default:
        return 'text-gray-700 bg-gray-100';
    }
  };

  if (compact) {
    return (
      <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white">
        <div className="flex justify-between items-start">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-900 mb-1">
              {lead.address || lead.name || 'Unnamed Lead'}
            </h3>
            <div className="flex items-center space-x-3 text-xs text-gray-600 mb-1">
              {lead.owner_name && (
                <div className="flex items-center space-x-1">
                  <User className="w-3 h-3" />
                  <span className="font-medium">{lead.owner_name}</span>
                </div>
              )}
              {lead.contractor_name && (
                <div className="flex items-center space-x-1">
                  <HardHat className="w-3 h-3" />
                  <span>{lead.contractor_name}</span>
                </div>
              )}
            </div>
            {lead.external_permit_id && (
              <div className="text-xs text-gray-500 mb-1">
                Permit #: {lead.external_permit_id}
              </div>
            )}
            <div className="flex items-center space-x-4 text-xs text-gray-600 mb-2">
              {lead.city && lead.state && (
                <div className="flex items-center space-x-1">
                  <MapPin className="w-3 h-3" />
                  <span>{lead.city}, {lead.state}</span>
                </div>
              )}
              {lead.service || lead.trade && (
                <span>{lead.service || lead.trade}</span>
              )}
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-900">
                {formatCurrency(lead.value)}
              </span>
              <span className="text-xs text-gray-500">
                {formatRelativeTime(lead.created_at)}
              </span>
            </div>
          </div>
          <div className="ml-3 flex flex-col items-end space-y-1">
            {lead.lead_score && (
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(lead.lead_score)}`}>
                {lead.lead_score}
              </span>
            )}
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(lead.status)}`}>
              {lead.status || 'new'}
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow bg-white">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {lead.address || lead.name || 'Unnamed Lead'}
            </h3>
            <div className="flex items-center space-x-3">
              {/* Lead Score */}
              {lead.lead_score && (
                <span className={`px-2 py-1 rounded-full text-sm font-medium ${getScoreColor(lead.lead_score)}`}>
                  Score: {lead.lead_score}
                </span>
              )}
              
              {/* Lead Score Label */}
              {lead.score_label && (
                <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-700">
                  {lead.score_label}
                </span>
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
          
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
            {lead.city && lead.state && (
              <div className="flex items-center space-x-1">
                <MapPin className="w-4 h-4" />
                <span>{lead.city}, {lead.state}</span>
              </div>
            )}
            {lead.service && (
              <div className="flex items-center space-x-1">
                <Building className="w-4 h-4" />
                <span>{lead.service}</span>
              </div>
            )}
            {lead.phone && (
              <div className="flex items-center space-x-1">
                <Phone className="w-4 h-4" />
                <span>{lead.phone}</span>
              </div>
            )}
            {lead.email && (
              <div className="flex items-center space-x-1">
                <Mail className="w-4 h-4" />
                <span>{lead.email}</span>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        {lead.owner_name && (
          <div>
            <span className="font-medium text-gray-500">Property Owner:</span>
            <p className="text-gray-900 flex items-center space-x-1">
              <User className="w-4 h-4 inline text-blue-600" />
              <span>{lead.owner_name}</span>
            </p>
          </div>
        )}

        {lead.contractor_name && (
          <div>
            <span className="font-medium text-gray-500">Contractor:</span>
            <p className="text-gray-900 flex items-center space-x-1">
              <HardHat className="w-4 h-4 inline text-amber-600" />
              <span>{lead.contractor_name}</span>
            </p>
          </div>
        )}

        {lead.lead_type && (
          <div>
            <span className="font-medium text-gray-500">Lead Type:</span>
            <p className="text-gray-900 capitalize">{lead.lead_type}</p>
          </div>
        )}

        {(lead.permit_id || lead.external_permit_id) && (
          <div>
            <span className="font-medium text-gray-500">Permit ID:</span>
            <p className="text-gray-900">{lead.external_permit_id || lead.permit_id}</p>
          </div>
        )}
        
        <div>
          <span className="font-medium text-gray-500">Value:</span>
          <p className="text-gray-900">{formatCurrency(lead.value)}</p>
        </div>

        {lead.trade && (
          <div>
            <span className="font-medium text-gray-500">Trade:</span>
            <p className="text-gray-900">{lead.trade}</p>
          </div>
        )}
        
        <div>
          <span className="font-medium text-gray-500">Created:</span>
          <p className="text-gray-900">{formatDate(lead.created_at)}</p>
        </div>
        
        <div>
          <span className="font-medium text-gray-500">Status:</span>
          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(lead.status)}`}>
            {lead.status || 'new'}
          </span>
        </div>
        
        {lead.county && (
          <div>
            <span className="font-medium text-gray-500">County:</span>
            <p className="text-gray-900">{lead.county}</p>
          </div>
        )}
        
        {lead.source && (
          <div>
            <span className="font-medium text-gray-500">Source:</span>
            <p className="text-gray-900">{lead.source}</p>
          </div>
        )}

        {lead.county_population && (
          <div>
            <span className="font-medium text-gray-500">County Pop:</span>
            <p className="text-gray-900">{lead.county_population.toLocaleString()}</p>
          </div>
        )}

        {lead.updated_at && (
          <div>
            <span className="font-medium text-gray-500">Updated:</span>
            <p className="text-gray-900">{formatDate(lead.updated_at)}</p>
          </div>
        )}
      </div>
    </div>
  );
}