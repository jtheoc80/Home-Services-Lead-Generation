import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import LeadCard from '@/components/LeadCard'
import HealthStatus from '@/components/HealthStatus'

interface Lead {
  id: number
  jurisdiction: string
  permit_id: string
  address: string
  description: string
  work_class: string
  category: string
  status: string
  issue_date: string
  applicant: string
  owner: string
  value: number
  is_residential: boolean
  trade_tags: string[]
  budget_band: string
  lead_score: number
  created_at: string
}

interface FeedbackData {
  [leadId: number]: {
    rating: 'thumbs_up' | 'thumbs_down' | null
    submitted: boolean
  }
}

export default function Dashboard() {
  const [leads, setLeads] = useState<Lead[]>([])
  const [feedback, setFeedback] = useState<FeedbackData>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Mock data for development - in production this would come from API
  useEffect(() => {
    // Simulate API call with mock data
    const mockLeads: Lead[] = [
      {
        id: 1,
        jurisdiction: 'City of Houston',
        permit_id: 'R2024-00123',
        address: '1234 Oak Street, Houston, TX 77001',
        description: 'Kitchen remodel with new appliances and countertops',
        work_class: 'Residential',
        category: 'Alteration',
        status: 'Issued',
        issue_date: '2024-01-15',
        applicant: 'John Smith',
        owner: 'John Smith',
        value: 25000,
        is_residential: true,
        trade_tags: ['kitchen', 'plumbing', 'electrical'],
        budget_band: '$15-50k',
        lead_score: 85,
        created_at: '2024-01-15T10:30:00Z'
      },
      {
        id: 2,
        jurisdiction: 'City of Houston',
        permit_id: 'R2024-00124',
        address: '5678 Pine Avenue, Houston, TX 77002',
        description: 'Roof replacement after storm damage',
        work_class: 'Residential',
        category: 'Repair',
        status: 'Issued',
        issue_date: '2024-01-16',
        applicant: 'ABC Roofing Inc',
        owner: 'Sarah Johnson',
        value: 18500,
        is_residential: true,
        trade_tags: ['roofing'],
        budget_band: '$15-50k',
        lead_score: 92,
        created_at: '2024-01-16T09:15:00Z'
      },
      {
        id: 3,
        jurisdiction: 'City of Houston',
        permit_id: 'R2024-00125',
        address: '9012 Maple Drive, Houston, TX 77003',
        description: 'HVAC system replacement and ductwork',
        work_class: 'Residential',
        category: 'Mechanical',
        status: 'Issued',
        issue_date: '2024-01-17',
        applicant: 'Cool Air Services',
        owner: 'Michael Brown',
        value: 12000,
        is_residential: true,
        trade_tags: ['hvac'],
        budget_band: '$5-15k',
        lead_score: 78,
        created_at: '2024-01-17T14:20:00Z'
      },
      {
        id: 4,
        jurisdiction: 'City of Houston',
        permit_id: 'R2024-00126',
        address: '3456 Elm Street, Houston, TX 77004',
        description: 'Bathroom renovation with tile work',
        work_class: 'Residential',
        category: 'Alteration',
        status: 'Under Review',
        issue_date: '2024-01-18',
        applicant: 'Maria Garcia',
        owner: 'Maria Garcia',
        value: 8500,
        is_residential: true,
        trade_tags: ['bath', 'plumbing', 'electrical'],
        budget_band: '$5-15k',
        lead_score: 71,
        created_at: '2024-01-18T11:45:00Z'
      }
    ]

    setTimeout(() => {
      setLeads(mockLeads)
      setLoading(false)
    }, 1000)
  }, [])

  const handleFeedback = async (leadId: number, rating: 'thumbs_up' | 'thumbs_down') => {
    try {
      // Convert thumbs to API rating format
      const apiRating = rating === 'thumbs_up' ? 'quoted' : 'not_qualified'
      
      // For now, we'll just update local state since we don't have auth token
      // In production, this would make an API call to /api/feedback
      setFeedback(prev => ({
        ...prev,
        [leadId]: {
          rating: rating,
          submitted: true
        }
      }))

      console.log(`Feedback submitted for lead ${leadId}: ${rating} (${apiRating})`)
      
      // Mock API call would look like:
      /*
      const response = await fetch('/api/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${userToken}`
        },
        body: JSON.stringify({
          lead_id: leadId,
          rating: apiRating
        })
      })
      */
      
    } catch (error) {
      console.error('Error submitting feedback:', error)
      setError('Failed to submit feedback. Please try again.')
    }
  }

  return (
    <>
      <Head>
        <title>Dashboard - LeadLedgerPro</title>
        <meta name="description" content="Review and provide feedback on your leads" />
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <div>
                <Link href="/" className="text-blue-600 hover:text-blue-800 mr-4">
                  ← Back to Home
                </Link>
                <h1 className="text-2xl font-bold text-gray-900">Lead Dashboard</h1>
              </div>
              <div className="flex items-center space-x-4">
                <HealthStatus />
                <div className="text-sm text-gray-600">
                  {leads.length} leads available
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading leads...</p>
            </div>
          ) : leads.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600">No leads available at this time.</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Recent Leads
                </h2>
                <p className="text-gray-600 mb-6">
                  Review each lead and provide feedback using the thumbs up/down buttons. 
                  Your feedback helps improve our lead scoring model.
                </p>
                
                <div className="space-y-4">
                  {leads.map((lead) => (
                    <LeadCard
                      key={lead.id}
                      lead={lead}
                      feedback={feedback[lead.id]}
                      onFeedback={(rating) => handleFeedback(lead.id, rating)}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </>
  )
}