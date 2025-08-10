import React from 'react'

interface PublicDataDisclaimerProps {
  className?: string
}

export default function PublicDataDisclaimer({ className = '' }: PublicDataDisclaimerProps) {
  return (
    <div className={`bg-gray-50 border border-gray-200 rounded-lg p-4 ${className}`}>
      <h3 className="font-semibold text-gray-900 mb-2">Public Records Notice:</h3>
      <p className="text-gray-700 text-sm">
        LeadLedgerPro compiles information from publicly available building permit and inspection data. 
        While we strive for accuracy, we do not guarantee that the data is current, complete, or free 
        from errors. The issuance of a permit does not constitute an offer to contract or a request 
        for services.
      </p>
    </div>
  )
}