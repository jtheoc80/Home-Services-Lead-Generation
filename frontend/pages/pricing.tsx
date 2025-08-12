import React from 'react'
import Head from 'next/head'
import Link from 'next/link'
import Footer from '@/components/Footer'

const tiers = [
  { name: "Starter", price: "$29/mo", features: ["1 region", "500 exports/mo", "Email support"], id: "starter" },
  { name: "Pro", price: "$79/mo", features: ["3 regions", "5,000 exports/mo", "Priority support"], id: "pro" },
  { name: "Teams", price: "$199/mo", features: ["10 regions", "Unlimited exports", "Team seats"], id: "teams" },
];

export default function Pricing() {
  return (
    <>
      <Head>
        <title>Pricing — LeadLedger Pro</title>
        <meta name="description" content="Simple, transparent pricing for LeadLedger Pro" />
      </Head>
      
      <div className="min-h-screen bg-white flex flex-col">
        {/* Header */}
        <header className="bg-blue-600 text-white">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <Link href="/" className="text-2xl font-bold">LeadLedgerPro</Link>
              <nav className="space-x-4">
                <Link href="/dashboard" className="border border-white px-4 py-2 rounded hover:bg-blue-700">
                  Dashboard
                </Link>
                <Link href="/pricing" className="hover:text-blue-700 focus:ring-2 focus:ring-blue-500">
                  Pricing
                </Link>
                <Link href="/signup" className="bg-white text-blue-600 px-4 py-2 rounded hover:bg-gray-100">
                  Sign Up
                </Link>
              </nav>
            </div>
          </div>
        </header>

        <main className="flex-1 mx-auto max-w-6xl px-6 py-16">
          <h1 className="text-4xl font-bold tracking-tight text-center">Simple, transparent pricing</h1>
          <p className="mt-3 text-center text-gray-600">Start free and upgrade when you're winning bids.</p>
          
          <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {tiers.map(t => (
              <div key={t.id} className="rounded-lg border p-6 flex flex-col">
                <div className="text-xl font-semibold">{t.name}</div>
                <div className="mt-2 text-3xl font-bold">{t.price}</div>
                <ul className="mt-4 space-y-2 text-sm">
                  {t.features.map((f, i) => (<li key={i}>• {f}</li>))}
                </ul>
                <Link 
                  href={`/signup?plan=${t.id}`} 
                  className="mt-6 rounded-md bg-indigo-600 px-4 py-2 text-white text-center font-semibold hover:bg-indigo-700 focus:ring-2 focus:ring-indigo-500"
                >
                  Start free trial
                </Link>
              </div>
            ))}
          </div>
          
          <section className="mt-12 text-sm text-gray-600">
            <h2 className="font-medium text-lg mb-4">Fair-use Policy</h2>
            <p className="mb-4">Our pricing is designed to be fair and transparent. Export limits are based on typical usage patterns to ensure service quality for all users.</p>
            
            <h2 className="font-medium text-lg mb-4">FAQ</h2>
            <div className="space-y-3">
              <div>
                <p><strong>Where do leads come from?</strong></p>
                <p>Public permit records from county/city systems, normalized hourly.</p>
              </div>
              <div>
                <p><strong>Do you contact homeowners?</strong></p>
                <p>No—this is a data tool; you control outreach.</p>
              </div>
              <div>
                <p><strong>Can I cancel?</strong></p>
                <p>Yes, anytime. No contracts.</p>
              </div>
            </div>
          </section>
        </main>

        <Footer />
      </div>
    </>
  )
}