import React, { useState, useEffect } from 'react';
import analytics from '../lib/analytics';

interface CancelSubscriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: CancellationData) => void;
  currentPlan?: string;
  currentRegion?: string;
  subscription?: {
    plan: string;
    status: string;
    trial_or_paid: 'trial' | 'paid';
  };
}

interface CancellationData {
  reason: string;
  notes: string;
  effective_at: 'immediately' | 'end_of_period';
}

const cancelReasons = [
  { value: 'too_expensive', label: 'Too expensive' },
  { value: 'not_using', label: 'Not using the service' },
  { value: 'poor_quality', label: 'Poor lead quality' },
  { value: 'switching_provider', label: 'Switching to another provider' },
  { value: 'business_closed', label: 'Business closed/paused' },
  { value: 'technical_issues', label: 'Technical issues' },
  { value: 'other', label: 'Other' },
];

export default function CancelSubscriptionModal({
  isOpen,
  onClose,
  onConfirm,
  currentPlan = 'unknown',
  currentRegion = 'unknown',
  subscription
}: CancelSubscriptionModalProps) {
  const [step, setStep] = useState<'reason' | 'details' | 'confirm'>('reason');
  const [selectedReason, setSelectedReason] = useState('');
  const [notes, setNotes] = useState('');
  const [effectiveAt, setEffectiveAt] = useState<'immediately' | 'end_of_period'>('end_of_period');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Track modal open
  useEffect(() => {
    if (isOpen) {
      analytics.track('cancel.clicked', {
        plan: currentPlan,
        current_region: currentRegion,
        trial_or_paid: subscription?.trial_or_paid || 'unknown',
        timestamp: new Date().toISOString()
      });
    }
  }, [isOpen, currentPlan, currentRegion, subscription?.trial_or_paid]);

  // Handle reason selection
  const handleReasonChange = (reason: string) => {
    setSelectedReason(reason);
    analytics.track('cancel.reason_selected', {
      reason,
      plan: currentPlan,
      timestamp: new Date().toISOString()
    });
  };

  // Handle notes input
  const handleNotesChange = (value: string) => {
    setNotes(value);
    analytics.track('cancel.notes_added', {
      notes_length: value.length,
      plan: currentPlan,
      timestamp: new Date().toISOString()
    });
  };

  // Handle cancellation confirmation
  const handleConfirm = async () => {
    setIsSubmitting(true);
    
    const cancellationData: CancellationData = {
      reason: selectedReason,
      notes,
      effective_at: effectiveAt
    };

    try {
      analytics.track('cancel.confirmed', {
        reason: selectedReason,
        notes_length: notes.length,
        plan: currentPlan,
        effective_at: effectiveAt,
        trial_or_paid: subscription?.trial_or_paid || 'unknown',
        timestamp: new Date().toISOString()
      });

      await onConfirm(cancellationData);
    } catch (error) {
      console.error('Cancellation failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle modal close without confirmation
  const handleClose = () => {
    if (step !== 'reason' || selectedReason) {
      // Only track abort if user has started the process
      analytics.track('cancel.abort', {
        plan: currentPlan,
        current_region: currentRegion,
        step_abandoned: step,
        reason_selected: selectedReason || null,
        timestamp: new Date().toISOString()
      });
    }

    // Reset state
    setStep('reason');
    setSelectedReason('');
    setNotes('');
    setEffectiveAt('end_of_period');
    setIsSubmitting(false);
    
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Cancel Subscription
            </h2>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
              disabled={isSubmitting}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {step === 'reason' && (
            <div>
              <p className="text-gray-600 mb-4">
                We&apos;re sorry to see you go. Please help us understand why you&apos;re canceling:
              </p>
              <div className="space-y-2">
                {cancelReasons.map((reason) => (
                  <label key={reason.value} className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="cancelReason"
                      value={reason.value}
                      checked={selectedReason === reason.value}
                      onChange={(e) => handleReasonChange(e.target.value)}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-700">{reason.label}</span>
                  </label>
                ))}
              </div>
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={handleClose}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Keep Subscription
                </button>
                <button
                  onClick={() => setStep('details')}
                  disabled={!selectedReason}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {step === 'details' && (
            <div>
              <p className="text-gray-600 mb-4">
                Please provide any additional details (optional):
              </p>
              <textarea
                value={notes}
                onChange={(e) => handleNotesChange(e.target.value)}
                placeholder="Tell us more about your experience..."
                className="w-full p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={4}
              />
              
              <div className="mt-4">
                <p className="text-gray-700 mb-2">When should the cancellation take effect?</p>
                <div className="space-y-2">
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="effectiveAt"
                      value="end_of_period"
                      checked={effectiveAt === 'end_of_period'}
                      onChange={(e) => setEffectiveAt(e.target.value as 'end_of_period')}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-700">End of current billing period</span>
                  </label>
                  <label className="flex items-center space-x-3 cursor-pointer">
                    <input
                      type="radio"
                      name="effectiveAt"
                      value="immediately"
                      checked={effectiveAt === 'immediately'}
                      onChange={(e) => setEffectiveAt(e.target.value as 'immediately')}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-gray-700">Immediately</span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setStep('reason')}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Back
                </button>
                <button
                  onClick={() => setStep('confirm')}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
                >
                  Continue
                </button>
              </div>
            </div>
          )}

          {step === 'confirm' && (
            <div>
              <div className="mb-4">
                <h3 className="text-lg font-medium text-gray-900 mb-2">Confirm Cancellation</h3>
                <p className="text-gray-600">
                  Are you sure you want to cancel your {currentPlan} subscription?
                </p>
                {effectiveAt === 'immediately' && (
                  <p className="text-red-600 text-sm mt-2">
                    Your subscription will be canceled immediately and you will lose access to all features.
                  </p>
                )}
                {effectiveAt === 'end_of_period' && (
                  <p className="text-yellow-600 text-sm mt-2">
                    Your subscription will remain active until the end of your current billing period.
                  </p>
                )}
              </div>

              <div className="bg-gray-50 p-4 rounded-md mb-4">
                <p className="text-sm text-gray-700">
                  <strong>Reason:</strong> {cancelReasons.find(r => r.value === selectedReason)?.label}
                </p>
                {notes && (
                  <p className="text-sm text-gray-700 mt-1">
                    <strong>Notes:</strong> {notes}
                  </p>
                )}
                <p className="text-sm text-gray-700 mt-1">
                  <strong>Effective:</strong> {effectiveAt === 'immediately' ? 'Immediately' : 'End of billing period'}
                </p>
              </div>

              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => setStep('details')}
                  disabled={isSubmitting}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors disabled:opacity-50"
                >
                  Back
                </button>
                <button
                  onClick={handleConfirm}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors disabled:bg-red-400 disabled:cursor-not-allowed"
                >
                  {isSubmitting ? 'Canceling...' : 'Confirm Cancellation'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}