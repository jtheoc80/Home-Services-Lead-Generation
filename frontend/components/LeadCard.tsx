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
    <div className="border-2 border-gray-200 rounded-xl overflow-hidden hover:shadow-lg transition-all duration-200 bg-white hover:border-navy-300">
      {/* Top Banner - Score, Status, and Lead Type */}
      <div className="bg-gradient-to-r from-navy-50 to-slate-50 px-6 py-3 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {/* Lead Score with Label */}
            {lead.lead_score && (
              <div className="flex items-center space-x-2">
                <span className={`px-3 py-1.5 rounded-lg text-sm font-bold ${getScoreColor(lead.lead_score)}`}>
                  {lead.lead_score}
                </span>
                {lead.score_label && (
                  <span className="px-2 py-1 rounded-md text-xs font-semibold bg-gray-700 text-white uppercase tracking-wide">
                    {lead.score_label}
                  </span>
                )}
              </div>
            )}
            
            {/* Lead Type Badge */}
            {lead.lead_type && (
              <span className="px-3 py-1 rounded-lg text-xs font-semibold bg-blue-100 text-blue-700 capitalize border border-blue-200">
                {lead.lead_type} Lead
              </span>
            )}
          </div>
          
          {/* Status */}
          <span className={`px-3 py-1.5 rounded-lg text-xs font-semibold uppercase ${getStatusColor(lead.status)}`}>
            {lead.status || 'new'}
          </span>
        </div>
      </div>

      <div className="p-6">
        {/* Address and Location */}
        <div className="mb-4">
          <h3 className="text-xl font-bold text-gray-900 mb-2">
            {lead.address || lead.name || 'Unnamed Lead'}
          </h3>
          <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600">
            {lead.county && (
              <div className="flex items-center space-x-1">
                <MapPin className="w-4 h-4 text-navy-600" />
                <span className="font-medium">{lead.county} County</span>
              </div>
            )}
            {lead.zipcode && (
              <span className="text-gray-500">ZIP: {lead.zipcode}</span>
            )}
            {formatRelativeTime(lead.created_at) && (
              <span className="text-gray-400">• {formatRelativeTime(lead.created_at)}</span>
            )}
          </div>
        </div>

        {/* Main Content Grid - Owner/Contractor and Key Details */}
        <div className="grid md:grid-cols-2 gap-6 mb-4">
          {/* Left Column - Contact Information */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Contact Information</h4>
            
            {lead.owner_name && (
              <div className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
                <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                  <User className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-blue-600 mb-0.5">Property Owner</div>
                  <div className="text-sm font-semibold text-gray-900 truncate">{lead.owner_name}</div>
                  {lead.phone && (
                    <div className="flex items-center space-x-1 mt-1 text-xs text-gray-600">
                      <Phone className="w-3 h-3" />
                      <span>{lead.phone}</span>
                    </div>
                  )}
                  {lead.email && (
                    <div className="flex items-center space-x-1 mt-1 text-xs text-gray-600">
                      <Mail className="w-3 h-3" />
                      <span className="truncate">{lead.email}</span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {lead.contractor_name && (
              <div className="flex items-start space-x-3 p-3 bg-amber-50 rounded-lg border border-amber-100">
                <div className="w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center flex-shrink-0">
                  <HardHat className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-amber-600 mb-0.5">Contractor</div>
                  <div className="text-sm font-semibold text-gray-900 truncate">{lead.contractor_name}</div>
                </div>
              </div>
            )}

            {!lead.owner_name && !lead.contractor_name && (
              <div className="flex items-center space-x-2 p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm text-gray-500">
                <User className="w-4 h-4" />
                <span>Contact information not available</span>
              </div>
            )}
          </div>

          {/* Right Column - Permit Details */}
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Permit Details</h4>
            
            <div className="grid grid-cols-2 gap-3">
              {/* Permit Value */}
              <div className="p-3 bg-green-50 rounded-lg border border-green-100">
                <div className="text-xs font-medium text-green-600 mb-1">Project Value</div>
                <div className="text-lg font-bold text-green-700">{formatCurrency(lead.value)}</div>
              </div>

              {/* Trade */}
              {lead.trade && (
                <div className="p-3 bg-purple-50 rounded-lg border border-purple-100">
                  <div className="text-xs font-medium text-purple-600 mb-1">Trade</div>
                  <div className="text-sm font-semibold text-purple-700 truncate">{lead.trade}</div>
                </div>
              )}

              {/* Permit ID */}
              {(lead.permit_id || lead.external_permit_id) && (
                <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 col-span-2">
                  <div className="text-xs font-medium text-gray-500 mb-1">Permit ID</div>
                  <div className="text-sm font-mono text-gray-700">{lead.external_permit_id || lead.permit_id}</div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Feedback Section */}
        {feedback?.submitted && (
          <div className={`mb-4 inline-flex items-center px-3 py-2 rounded-lg text-sm font-medium ${
            feedback.rating === 'thumbs_up' 
              ? 'bg-green-100 text-green-800 border border-green-200'
              : 'bg-red-100 text-red-800 border border-red-200'
          }`}>
            Feedback: {feedback.rating === 'thumbs_up' ? '👍 Good lead' : '👎 Poor lead'}
          </div>
        )}
      </div>
    </div>
  );
}