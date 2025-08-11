import React from 'react'
import Head from 'next/head'
import Link from 'next/link'
import Footer from '@/components/Footer'
import PublicDataDisclaimer from '@/components/PublicDataDisclaimer'

export default function Home() {
  return (
    <>
      <Head>
        <title>LeadLedgerPro - Home Services Lead Generation</title>
        <meta name="description" content="Quality home service leads from public permit data" />
      </Head>
      
      <div className="min-h-screen bg-white flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 text-white">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <h1 className="text-2xl font-bold">LeadLedgerPro</h1>
              <nav className="space-x-4">
                <Link href="/dashboard" className="border border-white px-4 py-2 rounded hover:bg-blue-700">
                  Dashboard
                </Link>
                <Link href="/signup" className="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100">
                  Sign Up
                </Link>
                <Link href="/payment" className="border border-white px-4 py-2 rounded hover:bg-blue-700">
                  Demo Payment
                </Link>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="flex-1">
          <div className="max-w-7xl mx-auto px-4 py-12">
            <div className="text-center mb-12">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Quality Home Service Leads
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                Connect with homeowners who need your services using public permit data
              </p>
              
              <div className="flex justify-center space-x-4">
                <Link 
                  href="/signup"
                  className="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg font-medium hover:bg-blue-700"
                >
                  Get Started
                </Link>
                <Link 
                  href="/terms"
                  className="border border-gray-300 text-gray-700 px-6 py-3 rounded-lg text-lg font-medium hover:bg-gray-50"
                >
                  Learn More
                </Link>
              </div>
            </div>

            {/* Features */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
              <div className="text-center">
                <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Verified Data</h3>
                <p className="text-gray-600">
                  Leads sourced from official building permit databases
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Targeted Leads</h3>
                <p className="text-gray-600">
                  Filtered by trade, location, and project value
                </p>
              </div>
              
              <div className="text-center">
                <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-semibold mb-2">Real-Time Updates</h3>
                <p className="text-gray-600">
                  Fresh leads delivered as permits are issued
                </p>
              </div>
            </div>

            {/* Public Data Disclaimer */}
            <div className="max-w-4xl mx-auto">
              <PublicDataDisclaimer />
            </div>
          </div>
        </main>

        {/* Footer */}
        <Footer />
      </div>
    </>
  )
}