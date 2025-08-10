import React from 'react'
import Head from 'next/head'
import PublicDataDisclaimer from '@/components/PublicDataDisclaimer'

export default function Terms() {
  return (
    <>
      <Head>
        <title>Terms of Service - LeadLedgerPro</title>
        <meta name="description" content="LeadLedgerPro Terms of Service" />
      </Head>
      
      <div className="min-h-screen bg-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Terms of Service</h1>
          
          <p className="text-lg text-gray-700 mb-8">
            By using LeadLedgerPro, you agree to these Terms of Service. Please read carefully 
            before purchasing or accessing any leads.
          </p>

          <PublicDataDisclaimer className="mb-8" />

          <div className="space-y-8">
            <section id="public-records-notice">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Public Records Notice</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  LeadLedgerPro sources its lead data from publicly available building permit records, 
                  inspection databases, and municipal filings. This information is:
                </p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Compiled from government websites and public databases</li>
                  <li>Subject to errors, delays, or incompleteness from the original sources</li>
                  <li>Not verified for accuracy or current status by LeadLedgerPro</li>
                  <li>Available to anyone with access to public records</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Solicitation Compliance</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  You are solely responsible for complying with all applicable laws when contacting leads, including:
                </p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>Do Not Call Registry:</strong> Check and respect federal and state do-not-call lists</li>
                  <li><strong>CAN-SPAM Act:</strong> Follow email marketing regulations if contacting via email</li>
                  <li><strong>Local Solicitation Laws:</strong> Comply with city and county door-to-door sales ordinances</li>
                  <li><strong>Professional Licensing:</strong> Ensure you have proper contractor licenses before offering services</li>
                </ul>
                <p>
                  LeadLedgerPro does not screen leads against do-not-call lists or verify contact preferences.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Payment & Refund Policy</h2>
              <div className="text-gray-700 space-y-4">
                <p><strong>Payment Processing:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>We accept USD payments via credit card (processed by Stripe)</li>
                  <li>Cryptocurrency payments are accepted (Bitcoin, Ethereum, etc.)</li>
                  <li>All prices are in USD; crypto amounts are calculated at time of checkout</li>
                </ul>
                
                <p><strong>Refund Policy:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Lead purchases are generally non-refundable due to the instant nature of data delivery</li>
                  <li>Technical issues or duplicate charges may qualify for refunds at our discretion</li>
                  <li>Cryptocurrency payments are non-reversible by nature</li>
                  <li>Refund requests must be submitted within 7 days of purchase</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Limitation of Liability</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  LeadLedgerPro provides lead data "as-is" without warranties of any kind. We specifically disclaim:
                </p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>Data Accuracy:</strong> No guarantee that permit data reflects actual customer needs</li>
                  <li><strong>Lead Quality:</strong> No assurance that contacts will result in business opportunities</li>
                  <li><strong>Contact Information:</strong> Phone numbers and addresses may be outdated or incorrect</li>
                  <li><strong>Business Results:</strong> No guarantee of sales, contracts, or revenue from purchased leads</li>
                </ul>
                
                <p>
                  Our total liability for any claim related to purchased leads shall not exceed the amount 
                  paid for those specific leads.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Licensing and Misuse</h2>
              <div className="text-gray-700 space-y-4">
                <p><strong>Prohibited Uses:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Reselling or redistributing lead data to third parties</li>
                  <li>Using leads for any illegal or fraudulent purposes</li>
                  <li>Harassing or repeatedly contacting uninterested prospects</li>
                  <li>Scraping or automated extraction of data from our platform</li>
                </ul>
                
                <p>
                  <strong>Contractor Licensing:</strong> You warrant that you hold all necessary licenses 
                  and permits required to legally offer home improvement services in your jurisdiction.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Governing Law and Jurisdiction</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  These Terms of Service are governed by the laws of the State of Texas, United States. 
                  Any disputes shall be resolved in the state or federal courts located in Harris County, Texas.
                </p>
                
                <p>
                  By using LeadLedgerPro, you consent to the jurisdiction of these courts and waive any 
                  objection to venue in Harris County, Texas.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Changes to Terms</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  We reserve the right to modify these Terms of Service at any time. Changes will be 
                  posted on this page with an updated effective date. Continued use of our service 
                  after changes constitutes acceptance of the new terms.
                </p>
                
                <p className="text-sm text-gray-500">
                  Last updated: {new Date().toLocaleDateString()}
                </p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </>
  )
}