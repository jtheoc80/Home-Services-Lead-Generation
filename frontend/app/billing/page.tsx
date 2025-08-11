'use client';

import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!);

interface Plan {
  key: string;
  name: string;
  price: number;
  features: string[];
  description: string;
  priceId?: string;
}

interface CreditBalance {
  user_id: string;
  balance: number;
  updated_at: string;
}

const plans: Plan[] = [
  {
    key: 'starter',
    name: 'Starter Contractor Plan',
    price: 199,
    features: [
      'Up to 25 leads per month',
      'Houston metro area coverage',
      'Basic lead scoring',
      'Email notifications',
      'Standard support'
    ],
    description: 'Perfect for small contractors getting started with lead generation'
  },
  {
    key: 'pro',
    name: 'Pro Contractor Plan',
    price: 399,
    features: [
      'Up to 100 leads per month',
      'Texas statewide coverage',
      'Advanced lead scoring',
      'Email & SMS notifications',
      'Priority support',
      'Export capabilities',
      'Advanced filtering'
    ],
    description: 'Best for growing contractors who need more leads and features'
  }
];

export default function BillingPage() {
  const [creditBalance, setCreditBalance] = useState<CreditBalance | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  useEffect(() => {
    fetchCreditBalance();
  }, []);

  const fetchCreditBalance = async () => {
    try {
      const response = await fetch('/api/billing/credits');
      if (response.ok) {
        const credits = await response.json();
        setCreditBalance(credits);
      }
    } catch (error) {
      console.error('Failed to fetch credit balance:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (plan: Plan) => {
    setActionLoading(`subscribe-${plan.key}`);
    
    try {
      // Create checkout session
      const response = await fetch('/api/billing/checkout/subscription', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          price_id: `price_${plan.key}`, // This would be the actual Stripe price ID
          quantity: 1
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const { checkout_url } = await response.json();
      
      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
      
    } catch (error) {
      console.error('Subscription failed:', error);
      alert('Failed to start subscription. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleBuyCredits = async () => {
    setActionLoading('credits');
    
    try {
      const response = await fetch('/api/billing/checkout/credits', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const { checkout_url } = await response.json();
      
      // Redirect to Stripe Checkout
      window.location.href = checkout_url;
      
    } catch (error) {
      console.error('Credit purchase failed:', error);
      alert('Failed to purchase credits. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleManageBilling = async () => {
    setActionLoading('portal');
    
    try {
      const response = await fetch('/api/billing/portal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error('Failed to create portal session');
      }

      const { portal_url } = await response.json();
      
      // Redirect to Stripe Customer Portal
      window.location.href = portal_url;
      
    } catch (error) {
      console.error('Portal access failed:', error);
      alert('Failed to access billing portal. Please try again.');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading billing information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 sm:text-4xl">
            Choose Your Plan
          </h1>
          <p className="mt-4 text-lg text-gray-600">
            Select the perfect plan for your lead generation needs
          </p>
        </div>

        {/* Credit Balance */}
        {creditBalance && (
          <div className="mt-8 max-w-md mx-auto">
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <h3 className="text-lg font-medium text-gray-900">Credit Balance</h3>
              <p className="text-3xl font-bold text-blue-600 mt-2">
                {creditBalance.balance} credits
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Last updated: {new Date(creditBalance.updated_at).toLocaleDateString()}
              </p>
            </div>
          </div>
        )}

        {/* Plans */}
        <div className="mt-12 grid gap-8 lg:grid-cols-2 lg:gap-12">
          {plans.map((plan) => (
            <div key={plan.key} className="bg-white rounded-lg shadow-lg p-8">
              <div className="text-center">
                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                <p className="mt-2 text-gray-600">{plan.description}</p>
                <div className="mt-4">
                  <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                  <span className="text-gray-600">/month</span>
                </div>
              </div>

              <ul className="mt-8 space-y-4">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <svg className="h-5 w-5 text-green-500 mr-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <div className="mt-8">
                <button
                  onClick={() => handleSubscribe(plan)}
                  disabled={actionLoading === `subscribe-${plan.key}`}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading === `subscribe-${plan.key}` ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Processing...
                    </span>
                  ) : (
                    `Subscribe to ${plan.name}`
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Options */}
        <div className="mt-12 max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h3 className="text-xl font-bold text-gray-900 text-center mb-6">
              Additional Options
            </h3>
            
            <div className="grid gap-6 md:grid-cols-2">
              {/* Buy Credits */}
              <div className="text-center">
                <h4 className="text-lg font-medium text-gray-900">Lead Credit Pack</h4>
                <p className="text-gray-600 mt-2">Need extra leads? Purchase additional credits</p>
                <div className="mt-4">
                  <span className="text-2xl font-bold text-gray-900">$49</span>
                  <span className="text-gray-600"> for 50 credits</span>
                </div>
                <button
                  onClick={handleBuyCredits}
                  disabled={actionLoading === 'credits'}
                  className="mt-4 bg-green-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading === 'credits' ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Processing...
                    </span>
                  ) : (
                    'Buy Credits'
                  )}
                </button>
              </div>

              {/* Manage Billing */}
              <div className="text-center">
                <h4 className="text-lg font-medium text-gray-900">Manage Billing</h4>
                <p className="text-gray-600 mt-2">Update payment methods and view invoices</p>
                <button
                  onClick={handleManageBilling}
                  disabled={actionLoading === 'portal'}
                  className="mt-8 bg-gray-600 text-white py-2 px-6 rounded-lg font-medium hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading === 'portal' ? (
                    <span className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Loading...
                    </span>
                  ) : (
                    'Manage Billing'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}