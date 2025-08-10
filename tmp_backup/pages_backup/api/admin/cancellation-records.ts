import { NextApiRequest, NextApiResponse } from 'next'

/**
 * Admin cancellation records API endpoint
 * 
 * Provides admin access to view cancellation records with reasons and notes.
 * Supports filtering and pagination.
 * 
 * GET /api/admin/cancellation-records
 * Query params:
 *   - admin_user_id: string (required)
 *   - cancellation_type?: 'trial' | 'paid'
 *   - reason_category?: string
 *   - start_date?: string (ISO date)
 *   - end_date?: string (ISO date)
 *   - page?: number
 *   - limit?: number
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ 
      success: false, 
      error: 'Method not allowed' 
    })
  }

  try {
    const { 
      admin_user_id, 
      cancellation_type, 
      reason_category, 
      start_date, 
      end_date,
      page = '1',
      limit = '25'
    } = req.query

    // Validate required fields
    if (!admin_user_id || typeof admin_user_id !== 'string') {
      return res.status(400).json({
        success: false,
        error: 'admin_user_id is required'
      })
    }

    // Check admin permissions
    if (!isAdminUser(admin_user_id)) {
      return res.status(403).json({
        success: false,
        error: 'Insufficient permissions'
      })
    }

    // In a real implementation, you would:
    // 1. Call the Python backend subscription API
    // 2. Apply filters and pagination
    // 3. Return formatted results
    
    // For demo purposes, simulate fetching cancellation records
    const filters = {
      cancellation_type: cancellation_type as string,
      reason_category: reason_category as string,
      start_date: start_date as string,
      end_date: end_date as string,
      page: parseInt(page as string),
      limit: parseInt(limit as string)
    }

    const recordsResult = await simulateGetCancellationRecords(filters)

    return res.status(200).json(recordsResult)

  } catch (error) {
    console.error('Admin cancellation records API error:', error)
    return res.status(500).json({
      success: false,
      error: 'Internal server error'
    })
  }
}

/**
 * Check if user has admin permissions
 */
function isAdminUser(userId: string): boolean {
  // Demo: users starting with "admin-" are considered admins
  return userId.startsWith('admin-')
}

/**
 * Simulate fetching cancellation records for demo purposes
 * In production, this would call the Python backend
 */
async function simulateGetCancellationRecords(filters: {
  cancellation_type?: string
  reason_category?: string
  start_date?: string
  end_date?: string
  page: number
  limit: number
}) {
  // Mock cancellation records data
  const mockRecords = [
    {
      id: 1,
      user_id: 'user-123-trial',
      subscription_id: 1,
      cancellation_type: 'trial',
      reason_category: 'not_satisfied',
      reason_notes: 'Service did not meet expectations. Lead quality was poor.',
      cancelled_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
      effective_date: new Date(Date.now() - 86400000).toISOString(),
      grace_period_days: 0,
      processed_by: null,
      refund_issued: false,
      refund_amount_cents: null
    },
    {
      id: 2,
      user_id: 'user-456-paid',
      subscription_id: 2,
      cancellation_type: 'paid',
      reason_category: 'cost',
      reason_notes: 'Too expensive for current business volume. May return when scaling up.',
      cancelled_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
      effective_date: new Date(Date.now() + 2592000000).toISOString(), // 30 days from cancellation
      grace_period_days: 30,
      processed_by: 'admin-support-1',
      refund_issued: false,
      refund_amount_cents: null
    },
    {
      id: 3,
      user_id: 'user-789-trial',
      subscription_id: 3,
      cancellation_type: 'trial',
      reason_category: 'found_alternative',
      reason_notes: 'Found a competitor with better pricing and features.',
      cancelled_at: new Date(Date.now() - 259200000).toISOString(), // 3 days ago
      effective_date: new Date(Date.now() - 259200000).toISOString(),
      grace_period_days: 0,
      processed_by: null,
      refund_issued: false,
      refund_amount_cents: null
    },
    {
      id: 4,
      user_id: 'user-321-paid',
      subscription_id: 4,
      cancellation_type: 'paid',
      reason_category: 'business_closure',
      reason_notes: 'Shutting down business operations due to retirement.',
      cancelled_at: new Date(Date.now() - 432000000).toISOString(), // 5 days ago
      effective_date: new Date(Date.now() + 2160000000).toISOString(), // 25 days from now
      grace_period_days: 30,
      processed_by: 'admin-support-2',
      refund_issued: true,
      refund_amount_cents: 2499
    }
  ]

  // Apply filters
  let filteredRecords = mockRecords

  if (filters.cancellation_type) {
    filteredRecords = filteredRecords.filter(
      record => record.cancellation_type === filters.cancellation_type
    )
  }

  if (filters.reason_category) {
    filteredRecords = filteredRecords.filter(
      record => record.reason_category === filters.reason_category
    )
  }

  // Apply pagination
  const startIndex = (filters.page - 1) * filters.limit
  const endIndex = startIndex + filters.limit
  const paginatedRecords = filteredRecords.slice(startIndex, endIndex)

  // Calculate summary statistics
  const totalRecords = filteredRecords.length
  const trialCancellations = filteredRecords.filter(r => r.cancellation_type === 'trial').length
  const paidCancellations = filteredRecords.filter(r => r.cancellation_type === 'paid').length
  const refundsIssued = filteredRecords.filter(r => r.refund_issued).length

  return {
    success: true,
    data: {
      records: paginatedRecords,
      pagination: {
        total_records: totalRecords,
        page: filters.page,
        limit: filters.limit,
        total_pages: Math.ceil(totalRecords / filters.limit)
      },
      summary: {
        total_cancellations: totalRecords,
        trial_cancellations: trialCancellations,
        paid_cancellations: paidCancellations,
        refunds_issued: refundsIssued
      }
    },
    status_code: 200
  }
}