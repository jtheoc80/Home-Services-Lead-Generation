import { useState } from 'react';
import CancelSubscriptionModal from '../components/CancelSubscriptionModal';
import ReactivationFlow from '../components/ReactivationFlow';

export default function AnalyticsDemo() {
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [subscriptionCanceled, setSubscriptionCanceled] = useState(false);

  const handleCancelConfirm = async (data: any) => {
    console.log('Cancellation data:', data);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setSubscriptionCanceled(true);
    setShowCancelModal(false);
  };

  const handleReactivate = async (data: any) => {
    console.log('Reactivation data:', data);
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    setSubscriptionCanceled(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8 text-center">
          Analytics Implementation Demo
        </h1>
        
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Analytics Features</h2>
          <ul className="list-disc list-inside space-y-2 text-gray-700">
            <li>Universal analytics wrapper supporting PostHog, Segment, Mixpanel, GA4</li>
            <li>Subscription cancellation tracking with reason and notes</li>
            <li>Reactivation flow tracking with timing analytics</li>
            <li>Server-side analytics logging to database</li>
            <li>Admin analytics dashboard API</li>
          </ul>
        </div>

        <div className="space-y-6">
          {!subscriptionCanceled ? (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-green-900 mb-2">
                Active Subscription
              </h3>
              <p className="text-green-700 mb-4">
                Your Basic plan is active. You have access to all features.
              </p>
              <button
                onClick={() => setShowCancelModal(true)}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-colors"
              >
                Cancel Subscription
              </button>
            </div>
          ) : (
            <ReactivationFlow
              onReactivate={handleReactivate}
              planBeforeCancel="Basic"
              canceledAt="2024-01-15T10:30:00Z"
              className="mb-6"
            />
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-blue-900 mb-2">
              Analytics Events
            </h3>
            <p className="text-blue-700 mb-4">
              Open the browser developer console to see analytics events being tracked.
            </p>
            <div className="space-y-2">
              <div className="text-sm text-blue-600">
                ✓ cancel.clicked - When modal opens
              </div>
              <div className="text-sm text-blue-600">
                ✓ cancel.reason_selected - When reason is chosen
              </div>
              <div className="text-sm text-blue-600">
                ✓ cancel.notes_added - When notes are typed
              </div>
              <div className="text-sm text-blue-600">
                ✓ cancel.confirmed - When cancellation is confirmed
              </div>
              <div className="text-sm text-blue-600">
                ✓ cancel.abort - When modal is closed without confirming
              </div>
              <div className="text-sm text-blue-600">
                ✓ reactivate.clicked - When reactivation is started
              </div>
              <div className="text-sm text-blue-600">
                ✓ reactivate.confirmed - When reactivation is completed
              </div>
            </div>
          </div>

          <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Environment Configuration
            </h3>
            <div className="text-sm text-gray-600 space-y-1">
              <div>Analytics Provider: {process.env.NEXT_PUBLIC_ANALYTICS_PROVIDER || 'none'}</div>
              <div>Current Mode: Development</div>
              <div>Events: Logged to console (provider not configured)</div>
            </div>
          </div>
        </div>

        <CancelSubscriptionModal
          isOpen={showCancelModal}
          onClose={() => setShowCancelModal(false)}
          onConfirm={handleCancelConfirm}
          currentPlan="Basic"
          currentRegion="Houston, TX"
          subscription={{
            plan: "Basic",
            status: "active",
            trial_or_paid: "paid"
          }}
        />
      </div>
    </div>
  );
}