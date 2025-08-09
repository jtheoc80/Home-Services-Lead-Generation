import React, { useState } from 'react'
import Head from 'next/head'
import CryptoPaymentDisclaimer from '@/components/CryptoPaymentDisclaimer'

export default function Payment() {
  const [paymentMethod, setPaymentMethod] = useState<'card' | 'crypto'>('card')

  return (
    <>
      <Head>
        <title>Payment - LeadLedgerPro</title>
        <meta name="description" content="Complete your LeadLedgerPro purchase" />
      </Head>
      
      <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md mx-auto">
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">Complete Your Purchase</h2>
            </div>
            
            <div className="px-6 py-4">
              {/* Order Summary */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Order Summary</h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Lead Package - Premium</span>
                    <span className="text-sm font-medium text-gray-900">$49.99</span>
                  </div>
                  <div className="flex justify-between items-center mt-2 pt-2 border-t border-gray-200">
                    <span className="text-sm font-medium text-gray-900">Total</span>
                    <span className="text-sm font-medium text-gray-900">$49.99</span>
                  </div>
                </div>
              </div>

              {/* Payment Method Selection */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-900 mb-3">Payment Method</h3>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    onClick={() => setPaymentMethod('card')}
                    className={`p-3 border rounded-lg text-sm font-medium ${
                      paymentMethod === 'card'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Credit Card
                  </button>
                  <button
                    onClick={() => setPaymentMethod('crypto')}
                    className={`p-3 border rounded-lg text-sm font-medium ${
                      paymentMethod === 'crypto'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Cryptocurrency
                  </button>
                </div>
              </div>

              {/* Crypto Payment Disclaimer */}
              {paymentMethod === 'crypto' && (
                <div className="mb-6">
                  <CryptoPaymentDisclaimer />
                </div>
              )}

              {/* Payment Form */}
              <div className="space-y-4">
                {paymentMethod === 'card' ? (
                  <>
                    <div>
                      <label htmlFor="card-number" className="block text-sm font-medium text-gray-700">
                        Card Number
                      </label>
                      <input
                        type="text"
                        id="card-number"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                        placeholder="1234 5678 9012 3456"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label htmlFor="expiry" className="block text-sm font-medium text-gray-700">
                          Expiry
                        </label>
                        <input
                          type="text"
                          id="expiry"
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          placeholder="MM/YY"
                        />
                      </div>
                      <div>
                        <label htmlFor="cvc" className="block text-sm font-medium text-gray-700">
                          CVC
                        </label>
                        <input
                          type="text"
                          id="cvc"
                          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          placeholder="123"
                        />
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div>
                      <label htmlFor="crypto-type" className="block text-sm font-medium text-gray-700">
                        Cryptocurrency
                      </label>
                      <select
                        id="crypto-type"
                        className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                      >
                        <option>Bitcoin (BTC)</option>
                        <option>Ethereum (ETH)</option>
                        <option>Litecoin (LTC)</option>
                      </select>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-4">
                      <p className="text-sm text-gray-600 mb-2">Send payment to:</p>
                      <p className="text-xs font-mono bg-white p-2 rounded border break-all">
                        1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa
                      </p>
                      <p className="text-sm text-gray-600 mt-2">
                        Amount: <span className="font-medium">0.00123 BTC</span>
                      </p>
                    </div>
                  </>
                )}
              </div>

              {/* Submit Button */}
              <div className="mt-6">
                <button
                  type="submit"
                  className="w-full bg-blue-600 border border-transparent rounded-md shadow-sm py-2 px-4 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  {paymentMethod === 'card' ? 'Pay $49.99' : 'I have sent the payment'}
                </button>
              </div>

              {/* Additional Disclaimer for USD Payments */}
              {paymentMethod === 'card' && (
                <div className="mt-4 text-xs text-gray-500 text-center">
                  Payments processed securely by Stripe. Your card information is never stored on our servers.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}