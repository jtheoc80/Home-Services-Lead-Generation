import React, { useState } from 'react';
import analytics from '../lib/analytics';

interface ReactivationFlowProps {
  onReactivate: (data: ReactivationData) => Promise<void>;
  planBeforeCancel?: string;
  canceledAt?: string;
  className?: string;
}

interface ReactivationData {
  plan: string;
  payment_provider: string;
}

export default function ReactivationFlow({
  onReactivate,
  planBeforeCancel = 'unknown',
  canceledAt,
  className = ''
}: ReactivationFlowProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(planBeforeCancel);

  // Calculate time since cancellation
  const getTimeSinceCancelDays = (): number => {
    if (!canceledAt) return 0;
    const cancelDate = new Date(canceledAt);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - cancelDate.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  };

  const handleReactivateClick = () => {
    const timeSinceCancelDays = getTimeSinceCancelDays();
    
    analytics.track('reactivate.clicked', {
      plan_before_cancel: planBeforeCancel,
      time_since_cancel_days: timeSinceCancelDays,
      timestamp: new Date().toISOString()
    });
  };

  const handleReactivateConfirm = async (paymentProvider: string) => {
    setIsSubmitting(true);
    
    try {
      const reactivationData: ReactivationData = {
        plan: selectedPlan,
        payment_provider: paymentProvider
      };

      await onReactivate(reactivationData);
      
      analytics.track('reactivate.confirmed', {
        plan: selectedPlan,
        payment_provider: paymentProvider,
        time_since_cancel_days: getTimeSinceCancelDays(),
        timestamp: new Date().toISOString()
      });
    } catch (error) {
      console.error('Reactivation failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-6 ${className}`}>
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-lg font-medium text-blue-900">
            Reactivate Your Subscription
          </h3>
          <p className="mt-2 text-blue-700">
            Welcome back! You previously had a {planBeforeCancel} subscription. 
            Would you like to reactivate your account?
          </p>
          
          {canceledAt && (
            <p className="mt-1 text-sm text-blue-600">
              Canceled {getTimeSinceCancelDays()} days ago
            </p>
          )}

          <div className="mt-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => {
                  handleReactivateClick();
                  handleReactivateConfirm('stripe');
                }}
                disabled={isSubmitting}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-blue-400 disabled:cursor-not-allowed transition-colors"
              >
                {isSubmitting ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Reactivating...
                  </>
                ) : (
                  'Reactivate with Stripe'
                )}
              </button>

              <button
                onClick={() => {
                  handleReactivateClick();
                  handleReactivateConfirm('crypto');
                }}
                disabled={isSubmitting}
                className="inline-flex items-center px-4 py-2 border border-blue-300 text-sm font-medium rounded-md text-blue-700 bg-white hover:bg-blue-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
              >
                Reactivate with Crypto
              </button>
            </div>
          </div>

          <div className="mt-3">
            <details className="text-sm">
              <summary className="text-blue-600 cursor-pointer hover:text-blue-800">
                What happens when I reactivate?
              </summary>
              <div className="mt-2 text-blue-700">
                <ul className="list-disc list-inside space-y-1">
                  <li>Your account will be immediately restored</li>
                  <li>You&apos;ll regain access to all features</li>
                  <li>Your previous settings and preferences will be preserved</li>
                  <li>Billing will resume according to your selected plan</li>
                </ul>
              </div>
            </details>
          </div>
        </div>
      </div>
    </div>
  );
}