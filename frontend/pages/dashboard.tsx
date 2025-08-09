import React, { useState, useEffect } from 'react'
import Head from 'next/head'
import Link from 'next/link'
import AreaSelector from '@/components/AreaSelector'

interface Permit {
  id: number
  permit_id: string
  jurisdiction: string
  address: string
  description: string
  value: number
  issue_date: string
  applicant: string
  owner: string
}

export default function Dashboard() {
  const [permits, setPermits] = useState<Permit[]>([])
  const [loading, setLoading] = useState(true)
  const [accountId] = useState('demo_user_123') // Mock account ID

  useEffect(() => {
    loadPermits()
  }, [])

  const loadPermits = async () => {
    try {
      // Mock permit data - in real implementation, this would call the backend API
      const mockPermits: Permit[] = [
        {
          id: 1,
          permit_id: "P2024-001",
          jurisdiction: "City of Houston",
          address: "1234 Heights Blvd, Houston, TX 77008",
          description: "Kitchen remodel with new cabinets and appliances",
          value: 25000,
          issue_date: "2024-01-15",
          applicant: "ABC Contractors",
          owner: "John Smith"
        },
        {
          id: 2,
          permit_id: "P2024-002", 
          jurisdiction: "City of Houston",
          address: "5678 River Oaks Dr, Houston, TX 77019",
          description: "Bathroom renovation and tile work",
          value: 15000,
          issue_date: "2024-01-14",
          applicant: "XYZ Remodeling",
          owner: "Jane Doe"
        },
        {
          id: 3,
          permit_id: "P2024-003",
          jurisdiction: "City of Houston", 
          address: "9876 Montrose St, Houston, TX 77006",
          description: "HVAC system replacement",
          value: 8000,
          issue_date: "2024-01-13",
          applicant: "Cool Air HVAC",
          owner: "Mike Johnson"
        },
        {
          id: 4,
          permit_id: "P2024-004",
          jurisdiction: "City of Houston",
          address: "2468 Downtown Ave, Houston, TX 77002", 
          description: "Roofing repair and replacement",
          value: 12000,
          issue_date: "2024-01-12",
          applicant: "Top Roof Solutions",
          owner: "Sarah Wilson"
        }
      ]
      
      setPermits(mockPermits)
    } catch (error) {
      console.error('Error loading permits:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFocusAreaSave = (focusArea: any) => {
    console.log('Focus area saved:', focusArea)
    // In real implementation, this would trigger a refresh of the permits list
    // with the new geographic filter applied
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(value)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return (
    <>
      <Head>
        <title>Dashboard - LeadLedgerPro</title>
        <meta name="description" content="Your personalized lead dashboard" />
      </Head>
      
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow">
          <div className="max-w-7xl mx-auto px-4 py-6">
            <div className="flex items-center justify-between">
              <div>
                <Link href="/" className="text-2xl font-bold text-blue-600">
                  LeadLedgerPro
                </Link>
                <p className="text-gray-600 mt-1">Lead Dashboard</p>
              </div>
              <nav className="space-x-4">
                <Link href="/" className="text-gray-600 hover:text-gray-900">
                  Home
                </Link>
                <Link href="/terms" className="text-gray-600 hover:text-gray-900">
                  Terms
                </Link>
              </nav>
            </div>
          </div>
        </header>

        <div className="max-w-7xl mx-auto px-4 py-8">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Area Selector Sidebar */}
            <div className="lg:col-span-1">
              <AreaSelector 
                accountId={accountId}
                onSave={handleFocusAreaSave}
              />
              
              {/* Stats Card */}
              <div className="bg-white rounded-lg shadow p-6 mt-6">
                <h3 className="text-lg font-semibold mb-4">Your Stats</h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Leads</span>
                    <span className="font-medium">{permits.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">This Week</span>
                    <span className="font-medium">{permits.length}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg. Project Value</span>
                    <span className="font-medium">
                      {permits.length > 0 
                        ? formatCurrency(permits.reduce((sum, p) => sum + p.value, 0) / permits.length)
                        : '$0'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Main Content */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                  <h2 className="text-xl font-semibold">Recent Leads</h2>
                  <p className="text-gray-600 text-sm mt-1">
                    Building permits matching your focus area
                  </p>
                </div>

                {loading ? (
                  <div className="p-8 text-center">
                    <div className="text-gray-500">Loading leads...</div>
                  </div>
                ) : permits.length === 0 ? (
                  <div className="p-8 text-center">
                    <div className="text-gray-500">No leads found for your current focus area.</div>
                    <p className="text-sm text-gray-400 mt-2">
                      Try expanding your geographic selection or check back later for new permits.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-gray-200">
                    {permits.map((permit) => (
                      <div key={permit.id} className="p-6 hover:bg-gray-50">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-2">
                              <h3 className="font-medium text-gray-900">
                                {permit.permit_id}
                              </h3>
                              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                {permit.jurisdiction}
                              </span>
                            </div>
                            
                            <p className="text-gray-600 mb-2">{permit.address}</p>
                            <p className="text-sm text-gray-500 mb-3">{permit.description}</p>
                            
                            <div className="grid grid-cols-2 gap-4 text-sm">
                              <div>
                                <span className="text-gray-500">Owner: </span>
                                <span className="font-medium">{permit.owner}</span>
                              </div>
                              <div>
                                <span className="text-gray-500">Contractor: </span>
                                <span className="font-medium">{permit.applicant}</span>
                              </div>
                            </div>
                          </div>
                          
                          <div className="text-right ml-4">
                            <div className="text-lg font-semibold text-green-600">
                              {formatCurrency(permit.value)}
                            </div>
                            <div className="text-sm text-gray-500">
                              {formatDate(permit.issue_date)}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Action Bar */}
              <div className="mt-6 bg-white rounded-lg shadow p-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-600">
                    Showing {permits.length} lead{permits.length !== 1 ? 's' : ''} from the last 7 days
                  </div>
                  <div className="space-x-2">
                    <button className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700">
                      Export CSV
                    </button>
                    <button className="border border-gray-300 text-gray-700 px-4 py-2 rounded text-sm hover:bg-gray-50">
                      Refresh
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}