import React from 'react'
import Link from 'next/link'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div className="col-span-1 md:col-span-2">
            <h3 className="text-xl font-bold mb-4">LeadLedgerPro</h3>
            <p className="text-gray-300 mb-4">
              Connecting home service contractors with qualified leads from public permit data.
            </p>
            <p className="text-gray-400 text-sm">
              © {new Date().getFullYear()} LeadLedgerPro. All rights reserved.
            </p>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Legal</h4>
            <ul className="space-y-2">
              <li>
                <Link 
                  href="/terms" 
                  className="text-gray-300 hover:text-white transition-colors"
                >
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link 
                  href="/privacy" 
                  className="text-gray-300 hover:text-white transition-colors"
                >
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link 
                  href="/terms#public-records-notice" 
                  className="text-gray-300 hover:text-white transition-colors"
                >
                  Public Data Notice
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact Info */}
          <div>
            <h4 className="text-lg font-semibold mb-4">Contact</h4>
            <ul className="space-y-2 text-gray-300">
              <li>support@leadledderpro.com</li>
              <li>privacy@leadledderpro.com</li>
            </ul>
          </div>
        </div>

        {/* Legal Notice */}
        <div className="border-t border-gray-700 mt-8 pt-8">
          <div className="text-sm text-gray-400 space-y-2">
            <p>
              <strong>Public Records Notice:</strong> LeadLedgerPro compiles information from publicly 
              available building permit data. Data accuracy is not guaranteed.
            </p>
            <p>
              <strong>Compliance:</strong> Users must comply with Do Not Call, CAN-SPAM, and local 
              solicitation laws. No guarantee of accuracy or job acquisition.
            </p>
          </div>
        </div>
      </div>
    </footer>
  )
}