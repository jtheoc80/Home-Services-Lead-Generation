import React from 'react'
import Head from 'next/head'

export default function Privacy() {
  return (
    <>
      <Head>
        <title>Privacy Policy - LeadLedgerPro</title>
        <meta name="description" content="LeadLedgerPro Privacy Policy" />
      </Head>
      
      <div className="min-h-screen bg-white">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">Privacy Policy</h1>
          
          <p className="text-lg text-gray-700 mb-8">
            This Privacy Policy describes how LeadLedgerPro collects, uses, and protects your information.
          </p>

          <div className="space-y-8">
            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Information We Collect</h2>
              <div className="text-gray-700 space-y-4">
                <p><strong>Account Information:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Name, email address, and phone number when you create an account</li>
                  <li>Company name and contractor license information</li>
                  <li>Billing address and payment method details</li>
                  <li>Service area preferences and trade specializations</li>
                </ul>
                
                <p><strong>Payment Information:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Credit card information (processed securely by Stripe, not stored by us)</li>
                  <li>Cryptocurrency wallet addresses for crypto payments</li>
                  <li>Transaction history and purchase records</li>
                </ul>

                <p><strong>Public Permit Data:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Building permit records from municipal databases</li>
                  <li>Property owner names and addresses from public records</li>
                  <li>Project descriptions and permit values</li>
                  <li>Contractor and applicant information from permits</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">How We Use Your Information</h2>
              <div className="text-gray-700 space-y-4">
                <p><strong>Lead Delivery:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Providing access to purchased lead data</li>
                  <li>Filtering leads based on your service area and trade preferences</li>
                  <li>Sending lead notifications and updates</li>
                </ul>
                
                <p><strong>Account Management:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Creating and maintaining your contractor account</li>
                  <li>Processing payments and managing subscriptions</li>
                  <li>Providing customer support and technical assistance</li>
                  <li>Sending important account and service updates</li>
                </ul>

                <p><strong>Service Improvement:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Analyzing usage patterns to improve our lead scoring algorithms</li>
                  <li>Understanding which types of leads are most valuable to contractors</li>
                  <li>Expanding to new geographic areas based on demand</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">How We Store and Secure Data</h2>
              <div className="text-gray-700 space-y-4">
                <p><strong>Data Storage:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>User account data is stored in secure cloud databases (Supabase)</li>
                  <li>Payment processing is handled by PCI-compliant third parties</li>
                  <li>Public permit data is cached for performance and historical analysis</li>
                  <li>All data is encrypted in transit and at rest</li>
                </ul>
                
                <p><strong>Security Measures:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>SSL/TLS encryption for all web traffic</li>
                  <li>Regular security audits and penetration testing</li>
                  <li>Access controls and authentication for all systems</li>
                  <li>Regular backups with secure off-site storage</li>
                </ul>

                <p><strong>Data Retention:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Account information retained while your account is active</li>
                  <li>Transaction records kept for 7 years for tax and legal compliance</li>
                  <li>Public permit data retained indefinitely as it remains publicly available</li>
                  <li>Marketing preferences and communications stored until you opt out</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibent text-gray-900 mb-4">Third-Party Services</h2>
              <div className="text-gray-700 space-y-4">
                <p>We use the following third-party services that may collect information:</p>
                
                <p><strong>Payment Processing:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>Stripe:</strong> Credit card processing (subject to Stripe's privacy policy)</li>
                  <li><strong>Cryptocurrency Processors:</strong> For crypto payment handling</li>
                </ul>
                
                <p><strong>Infrastructure:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>Supabase:</strong> Database and authentication services</li>
                  <li><strong>Cloud Hosting:</strong> Application hosting and data storage</li>
                </ul>

                <p><strong>Analytics:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Usage analytics to improve our service (anonymized data only)</li>
                  <li>Error tracking for technical issue resolution</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Cookies and Session Handling</h2>
              <div className="text-gray-700 space-y-4">
                <p><strong>Essential Cookies:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Session cookies to keep you logged in</li>
                  <li>Authentication tokens for secure access</li>
                  <li>Shopping cart and checkout session data</li>
                </ul>
                
                <p><strong>Analytics Cookies:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Anonymous usage tracking to improve our service</li>
                  <li>Performance monitoring to identify and fix issues</li>
                </ul>

                <p><strong>Cookie Control:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>You can disable cookies in your browser settings</li>
                  <li>Essential cookies are required for the service to function</li>
                  <li>Analytics cookies can be opted out without affecting functionality</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Your Rights</h2>
              <div className="text-gray-700 space-y-4">
                <p>You have the following rights regarding your personal information:</p>
                
                <p><strong>Access and Portability:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Request a copy of all personal data we have about you</li>
                  <li>Download your account information and purchase history</li>
                </ul>
                
                <p><strong>Correction and Deletion:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Update your account information at any time</li>
                  <li>Request deletion of your account and associated data</li>
                  <li>Note: Public permit data cannot be deleted as it remains publicly available</li>
                </ul>

                <p><strong>Marketing Control:</strong></p>
                <ul className="list-disc pl-6 space-y-2">
                  <li>Opt out of marketing emails and notifications</li>
                  <li>Manage communication preferences in your account settings</li>
                </ul>

                <p>
                  To exercise these rights, contact us at privacy@leadledderpro.com with your request.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Data Sharing</h2>
              <div className="text-gray-700 space-y-4">
                <p><strong>We do not sell personal information to third parties.</strong></p>
                
                <p>We may share information in these limited circumstances:</p>
                <ul className="list-disc pl-6 space-y-2">
                  <li><strong>Service Providers:</strong> Third parties that help us operate our service (payment processors, hosting)</li>
                  <li><strong>Legal Requirements:</strong> When required by law or to protect our rights</li>
                  <li><strong>Business Transfers:</strong> In the event of a merger, acquisition, or sale of assets</li>
                </ul>

                <p>
                  <strong>Public Permit Data:</strong> The lead data we provide consists of public records 
                  that are already available to anyone through government websites and databases.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Children's Privacy</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  LeadLedgerPro is not intended for use by children under 18. We do not knowingly 
                  collect personal information from children under 18. If we become aware that a 
                  child under 18 has provided us with personal information, we will delete such 
                  information immediately.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Changes to This Privacy Policy</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  We may update this Privacy Policy from time to time. We will notify you of any 
                  changes by posting the new Privacy Policy on this page and updating the "Last updated" 
                  date below. You are advised to review this Privacy Policy periodically for any changes.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Contact Us</h2>
              <div className="text-gray-700 space-y-4">
                <p>
                  If you have any questions about this Privacy Policy or our data practices, 
                  please contact us at:
                </p>
                <ul className="list-none space-y-2">
                  <li><strong>Email:</strong> privacy@leadledderpro.com</li>
                  <li><strong>Address:</strong> LeadLedgerPro Privacy Team</li>
                </ul>
                
                <p className="text-sm text-gray-500 mt-8">
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