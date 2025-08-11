import { NextApiRequest, NextApiResponse } from 'next'

/**
 * Subscription cancellation API endpoint
 * 
 * Handles subscription cancellation requests with different workflows
 * for trial vs paid subscriptions.
 * 
 * POST /api/cancel-subscription
 * Body: {
 *   user_id: string
 *   reason_category?: string
 *   reason_notes?: string
 * }
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow POST requests
  if (req.method !== 'POST') {
    return res.status(405).json({ 
      success: false, 
      error: 'Method not allowed' 
    })
  }

  try {
    const { user_id, reason_category, reason_notes } = req.body

    // Validate required fields
    if (!user_id) {
      return res.status(400).json({
        success: false,
        error: 'user_id is required'
      })
    }

    // In a real implementation, you would:
    // 1. Call the Python backend subscription API
    // 2. Handle authentication/authorization
    // 3. Validate user permissions
    
    // For demo purposes, simulate the cancellation workflow
    const cancellationResult = await simulateCancellation({
      user_id,
      reason_category,
      reason_notes
    })

    return res.status(cancellationResult.status_code).json(cancellationResult)

  } catch (error) {
    console.error('Cancellation API error:', error)
    return res.status(500).json({
      success: false,
      error: 'Internal server error'
    })
  }
}

/**
 * Simulate cancellation workflow for demo purposes
 * In production, this would call the Python backend
 */
async function simulateCancellation(request: {
  user_id: string
  reason_category?: string
  reason_notes?: string
}) {
  // Mock subscription data based on user_id patterns
  const isTrialUser = request.user_id.includes('trial')
  const isPaidUser = request.user_id.includes('paid')
  
  if (isTrialUser) {
    // Trial cancellation - immediate termination
    return {
      success: true,
      data: {
        cancellation_type: 'trial',
        effective_date: new Date().toISOString(),
        grace_period_days: 0,
        message: 'Trial subscription cancelled immediately'
      },
      status_code: 200
    }
  } else if (isPaidUser) {
    // Paid cancellation - grace period
    const gracePeriodEnd = new Date()
    gracePeriodEnd.setDate(gracePeriodEnd.getDate() + 30)
    
    return {
      success: true,
      data: {
        cancellation_type: 'paid',
        effective_date: gracePeriodEnd.toISOString(),
        grace_period_days: 30,
        message: `Paid subscription cancelled. Access continues until ${gracePeriodEnd.toLocaleDateString()}`
      },
      status_code: 200
    }
  } else {
    // User not found
    return {
      success: false,
      error: 'Subscription not found',
      status_code: 404
    }
  }
}