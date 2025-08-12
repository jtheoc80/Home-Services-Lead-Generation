import React, { useState } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import CryptoPaymentDisclaimer from '@/components/CryptoPaymentDisclaimer'

export default function Signup() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    company: '',
    phone: '',
    paymentMethod: 'stripe' as 'stripe' | 'btc' | 'eth' | 'xrp',
    cryptoWalletAddress: '',
    agreeToTerms: false
  })

  const [errors, setErrors] = useState<{[key: string]: string}>({})

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    const checked = (e.target as HTMLInputElement).checked
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    const newErrors: {[key: string]: string} = {}
    
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required'
    }
    
    if (!formData.email.trim()) {
      newErrors.email = 'Email is required'
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email'
    }
    
    if (!formData.password.trim()) {
      newErrors.password = 'Password is required'
    } else if (formData.password.length < 8) {
      newErrors.password = 'Password must be at least 8 characters'
    }
    
    if (!formData.phone.trim()) {
      newErrors.phone = 'Phone number is required'
    }
    
    // Validate crypto wallet address for crypto payments
    if (formData.paymentMethod !== 'stripe' && !formData.cryptoWalletAddress.trim()) {
      newErrors.cryptoWalletAddress = 'Crypto wallet address is required for cryptocurrency payments'
    }
    
    if (!formData.agreeToTerms) {
      newErrors.agreeToTerms = 'You must agree to the Terms of Service and Privacy Policy'
    }
    
    setErrors(newErrors)
    
    if (Object.keys(newErrors).length === 0) {
      // Submit form - this would create the contractor with trial period
      const trialStartDate = new Date()
      const trialEndDate = new Date(trialStartDate)
      trialEndDate.setDate(trialEndDate.getDate() + 7) // 7-day trial
      
      const contractorData = {
        ...formData,
        trialStartDate: trialStartDate.toISOString(),
        trialEndDate: trialEndDate.toISOString(),
        subscriptionStatus: 'trial'
      }
      
      console.log('Trial signup submitted:', contractorData)
      alert('7-day free trial started! Welcome to LeadLedgerPro! (This is a demo)')
    }
  }

  return (
    <>
      <Head>
        <title>Sign Up - LeadLedgerPro</title>
        <meta name="description" content="Create your LeadLedgerPro contractor account" />
      </Head>
      
      <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          <h2 className="mt-6 text-center text-3xl font-bold text-gray-900">
            Start Your 7-Day Free Trial
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Full access to LeadLedgerPro • Payment method required • Cancel anytime
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
            <form className="space-y-6" onSubmit={handleSubmit}>
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                  Full Name *
                </label>
                <div className="mt-1">
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    value={formData.name}
                    onChange={handleChange}
                    aria-describedby={errors.name ? "name-error" : undefined}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.name && <p id="name-error" className="mt-1 text-sm text-red-600">{errors.name}</p>}
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                  Email Address *
                </label>
                <div className="mt-1">
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    aria-describedby={errors.email ? "email-error" : undefined}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.email && <p id="email-error" className="mt-1 text-sm text-red-600">{errors.email}</p>}
                </div>
              </div>

              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700">
                  Phone Number *
                </label>
                <div className="mt-1">
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    required
                    value={formData.phone}
                    onChange={handleChange}
                    aria-describedby={errors.phone ? "phone-error" : undefined}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.phone && <p id="phone-error" className="mt-1 text-sm text-red-600">{errors.phone}</p>}
                </div>
              </div>

              <div>
                <label htmlFor="company" className="block text-sm font-medium text-gray-700">
                  Company Name
                </label>
                <div className="mt-1">
                  <input
                    id="company"
                    name="company"
                    type="text"
                    value={formData.company}
                    onChange={handleChange}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                  Password *
                </label>
                <div className="mt-1">
                  <input
                    id="password"
                    name="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    aria-describedby={errors.password ? "password-error" : undefined}
                    className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  {errors.password && <p id="password-error" className="mt-1 text-sm text-red-600">{errors.password}</p>}
                </div>
              </div>

              {/* Payment Method Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Payment Method *
                </label>
                <p className="text-sm text-gray-600 mb-3">
                  <strong>7-day free trial</strong> - Required for trial registration. You won't be charged until your trial ends.
                </p>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  <button
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, paymentMethod: 'stripe' }))}
                    className={`p-3 border rounded-lg text-sm font-medium ${
                      formData.paymentMethod === 'stripe'
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    Credit Card (Stripe)
                  </button>
                  <div className="space-y-2">
                    <div className="grid grid-cols-3 gap-1">
                      {['btc', 'eth', 'xrp'].map((crypto) => (
                        <button
                          key={crypto}
                          type="button"
                          onClick={() => setFormData(prev => ({ ...prev, paymentMethod: crypto as any }))}
                          className={`p-2 border rounded text-xs font-medium ${
                            formData.paymentMethod === crypto
                              ? 'border-blue-500 bg-blue-50 text-blue-700'
                              : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                          }`}
                        >
                          {crypto.toUpperCase()}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Crypto Wallet Address Input */}
                {formData.paymentMethod !== 'stripe' && (
                  <div className="mt-3">
                    <label htmlFor="cryptoWalletAddress" className="block text-sm font-medium text-gray-700">
                      Your {formData.paymentMethod.toUpperCase()} Wallet Address *
                    </label>
                    <div className="mt-1">
                      <input
                        id="cryptoWalletAddress"
                        name="cryptoWalletAddress"
                        type="text"
                        required
                        value={formData.cryptoWalletAddress}
                        onChange={handleChange}
                        aria-describedby={errors.cryptoWalletAddress ? "crypto-error" : undefined}
                        className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                        placeholder="Enter your wallet address"
                      />
                      {errors.cryptoWalletAddress && <p id="crypto-error" className="mt-1 text-sm text-red-600">{errors.cryptoWalletAddress}</p>}
                    </div>
                  </div>
                )}

                {/* Crypto Payment Disclaimer */}
                {formData.paymentMethod !== 'stripe' && (
                  <div className="mt-3">
                    <CryptoPaymentDisclaimer />
                  </div>
                )}
              </div>

              {/* Consent Checkbox */}
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="agreeToTerms"
                    name="agreeToTerms"
                    type="checkbox"
                    checked={formData.agreeToTerms}
                    onChange={handleChange}
                    aria-describedby={errors.agreeToTerms ? "terms-error" : undefined}
                    className="focus:ring-blue-500 h-4 w-4 text-blue-600 border-gray-300 rounded"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="agreeToTerms" className="text-gray-700">
                    I agree to the{' '}
                    <Link 
                      href="/terms" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-500 underline"
                    >
                      Terms of Service
                    </Link>
                    {' '}and{' '}
                    <Link 
                      href="/privacy" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:text-blue-500 underline"
                    >
                      Privacy Policy
                    </Link>
                    {' '}*
                  </label>
                  {errors.agreeToTerms && (
                    <p id="terms-error" className="mt-1 text-sm text-red-600">{errors.agreeToTerms}</p>
                  )}
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={!formData.agreeToTerms}
                  className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                    formData.agreeToTerms 
                      ? 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500' 
                      : 'bg-gray-400 cursor-not-allowed'
                  }`}
                >
                  Start 7-Day Free Trial
                </button>
                <p className="mt-2 text-xs text-gray-600 text-center">
                  Trial includes full dashboard access. Auto-renews after 7 days unless canceled.
                </p>
              </div>
            </form>

            <div className="mt-6">
              <div className="text-center">
                <span className="text-sm text-gray-600">
                  Already have an account?{' '}
                  <Link href="/login" className="text-blue-600 hover:text-blue-500">
                    Sign in
                  </Link>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}