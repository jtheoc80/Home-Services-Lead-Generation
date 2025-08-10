import React, { useState } from 'react';

interface CancelSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: CancelData) => void;
  loading?: boolean;
}

interface CancelData {
  reason: string;
  reason_codes: string[];
  notes: string;
}

const CANCELLATION_REASONS = [
  { value: 'not_using', label: 'Not using the service enough' },
  { value: 'too_expensive', label: 'Too expensive' },
  { value: 'found_alternative', label: 'Found a better alternative' },
  { value: 'billing_issue', label: 'Billing issues' },
  { value: 'technical_issues', label: 'Technical problems' },
  { value: 'other', label: 'Other' }
];

const REASON_CODES = [
  'poor_results',
  'missing_features',
  'complex_interface',
  'slow_support',
  'data_accuracy',
  'integration_issues'
];

export default function CancelSubscriptionModal({
  isOpen,
  onClose,
  onConfirm,
  loading = false
}: CancelSubscriptionModalProps) {
  const [formData, setFormData] = useState<CancelData>({
    reason: '',
    reason_codes: [],
    notes: ''
  });

  const handleReasonChange = (reason: string) => {
    setFormData(prev => ({ ...prev, reason }));
  };

  const handleReasonCodeToggle = (code: string) => {
    setFormData(prev => ({
      ...prev,
      reason_codes: prev.reason_codes.includes(code)
        ? prev.reason_codes.filter(c => c !== code)
        : [...prev.reason_codes, code]
    }));
  };

  const handleNotesChange = (notes: string) => {
    setFormData(prev => ({ ...prev, notes }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.reason) {
      onConfirm(formData);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFormData({ reason: '', reason_codes: [], notes: '' });
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Cancel Subscription</h2>
          <button
            onClick={handleClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 disabled:cursor-not-allowed"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Reason Selection (Required) */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Why are you canceling? <span className="text-red-500">*</span>
            </label>
            <div className="space-y-2">
              {CANCELLATION_REASONS.map((reason) => (
                <label key={reason.value} className="flex items-center">
                  <input
                    type="radio"
                    name="reason"
                    value={reason.value}
                    checked={formData.reason === reason.value}
                    onChange={(e) => handleReasonChange(e.target.value)}
                    disabled={loading}
                    className="mr-2 text-blue-600 focus:ring-blue-500 disabled:cursor-not-allowed"
                  />
                  <span className="text-sm text-gray-900">{reason.label}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Reason Codes (Optional) */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Specific issues (optional)
            </label>
            <div className="flex flex-wrap gap-2">
              {REASON_CODES.map((code) => (
                <button
                  key={code}
                  type="button"
                  onClick={() => handleReasonCodeToggle(code)}
                  disabled={loading}
                  className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors disabled:cursor-not-allowed ${
                    formData.reason_codes.includes(code)
                      ? 'bg-blue-100 border-blue-300 text-blue-800'
                      : 'bg-gray-100 border-gray-300 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {code.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>

          {/* Notes (Optional) */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional feedback (optional)
            </label>
            <textarea
              value={formData.notes}
              onChange={(e) => handleNotesChange(e.target.value)}
              disabled={loading}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
              placeholder="Tell us how we could improve..."
            />
          </div>

          {/* Actions */}
          <div className="flex space-x-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={loading}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              Keep Subscription
            </button>
            <button
              type="submit"
              disabled={!formData.reason || loading}
              className="flex-1 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </>
              ) : (
                'Cancel Subscription'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}