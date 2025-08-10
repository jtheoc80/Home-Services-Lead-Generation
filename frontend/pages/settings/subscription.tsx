import React, { useState } from 'react';
import { useRouter } from 'next/router';
import CancelSubscriptionModal from '../../components/CancelSubscriptionModal';

interface CancelData {
  reason: string;
  reason_codes: string[];
  notes: string;
}

interface SubscriptionData {
  status: 'active' | 'canceled' | 'past_due';
  current_period_end?: string;
  effective_at?: string;
  plan_name?: string;
}

export default function SubscriptionPage() {
  const router = useRouter();
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [cancelResult, setCancelResult] = useState<{
    success: boolean;
    message: string;
    effective_at?: string;
  } | null>(null);

  // Mock subscription data - in real app, this would come from API/database
  const [subscription, setSubscription] = useState<SubscriptionData>({
    status: 'active',
    current_period_end: '2024-09-09',
    plan_name: 'LeadLedgerPro Premium'
  });

  const handleCancelConfirm = async (data: CancelData) => {
    setLoading(true);
    try {
      const response = await fetch('/api/subscription/cancel', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (result.success) {
        setCancelResult({
          success: true,
          message: result.message,
          effective_at: result.effective_at
        });
        setSubscription(prev => ({
          ...prev,
          status: 'canceled',
          effective_at: result.effective_at
        }));
        setShowCancelModal(false);
      } else {
        setCancelResult({
          success: false,
          message: result.error || 'Failed to cancel subscription'
        });
      }
    } catch (error) {
      setCancelResult({
        success: false,
        message: 'Network error. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReactivate = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/subscription/reactivate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();

      if (result.success) {
        setCancelResult({
          success: true,
          message: result.message
        });
        setSubscription(prev => ({
          ...prev,
          status: 'active',
          effective_at: undefined
        }));
      } else {
        setCancelResult({
          success: false,
          message: result.error || 'Failed to reactivate subscription'
        });
      }
    } catch (error) {
      setCancelResult({
        success: false,
        message: 'Network error. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const isEffectiveNow = (effectiveAt: string) => {
    const effective = new Date(effectiveAt);
    const now = new Date();
    return effective <= now;
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="mb-4 inline-flex items-center text-sm text-gray-500 hover:text-gray-700"
          >
            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Subscription Settings</h1>
        </div>

        {/* Cancellation Grace Period Banner */}
        {subscription.status === 'canceled' && subscription.effective_at && (
          <div className="mb-6 bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  <strong>Your access ends {formatDate(subscription.effective_at)}</strong>
                  {!isEffectiveNow(subscription.effective_at) && (
                    <span> - You can still reactivate your subscription before this date.</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Result Messages */}
        {cancelResult && (
          <div className={`mb-6 p-4 rounded-md ${
            cancelResult.success ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            <div className="flex">
              <div className="flex-shrink-0">
                {cancelResult.success ? (
                  <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                ) : (
                  <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium">{cancelResult.message}</p>
              </div>
            </div>
          </div>
        )}

        {/* Subscription Details Card */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-medium text-gray-900">Current Subscription</h2>
          </div>
          <div className="px-6 py-4">
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-500">Plan</span>
                <span className="text-sm text-gray-900">{subscription.plan_name}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-500">Status</span>
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                  subscription.status === 'active' 
                    ? 'bg-green-100 text-green-800'
                    : subscription.status === 'canceled'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {subscription.status === 'canceled' && subscription.effective_at && isEffectiveNow(subscription.effective_at)
                    ? 'Canceled'
                    : subscription.status === 'canceled'
                    ? 'Cancellation Scheduled'
                    : subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)
                  }
                </span>
              </div>
              {subscription.current_period_end && (
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-500">Current Period Ends</span>
                  <span className="text-sm text-gray-900">{formatDate(subscription.current_period_end)}</span>
                </div>
              )}
              {subscription.effective_at && (
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium text-gray-500">
                    {isEffectiveNow(subscription.effective_at) ? 'Canceled On' : 'Cancellation Effective'}
                  </span>
                  <span className="text-sm text-gray-900">{formatDate(subscription.effective_at)}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-6 flex space-x-4">
          {subscription.status === 'active' ? (
            <button
              onClick={() => setShowCancelModal(true)}
              disabled={loading}
              className="px-4 py-2 border border-red-300 text-red-700 bg-white rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
              Cancel Subscription
            </button>
          ) : subscription.status === 'canceled' && subscription.effective_at && !isEffectiveNow(subscription.effective_at) ? (
            <button
              onClick={handleReactivate}
              disabled={loading}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center"
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
                'Reactivate Subscription'
              )}
            </button>
          ) : null}
        </div>

        {/* Cancel Modal */}
        <CancelSubscriptionModal
          isOpen={showCancelModal}
          onClose={() => setShowCancelModal(false)}
          onConfirm={handleCancelConfirm}
          loading={loading}
        />
      </div>
    </div>
  );
}