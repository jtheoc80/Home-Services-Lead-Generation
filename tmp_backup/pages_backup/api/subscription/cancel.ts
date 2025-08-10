import { NextApiRequest, NextApiResponse } from 'next';

interface CancelRequestBody {
  reason: string;
  reason_codes?: string[];
  notes?: string;
}

interface CancelResponse {
  success: boolean;
  effective_at: string;
  subscription_status: string;
  message: string;
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<CancelResponse | { error: string }>
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    const { reason, reason_codes, notes } = req.body as CancelRequestBody;

    // Validate required fields
    if (!reason) {
      return res.status(400).json({ error: 'Reason is required' });
    }

    // For demo purposes, we'll simulate the cancellation logic
    // In a real implementation, this would:
    // 1. Authenticate the user
    // 2. Look up their subscription
    // 3. Process the cancellation
    // 4. Send notifications

    // Simulate effective date logic
    const now = new Date();
    const gracePeriodDays = 7; // Example: 7 days grace period
    const effectiveAt = new Date(now.getTime() + gracePeriodDays * 24 * 60 * 60 * 1000);
    
    // Determine if cancellation is immediate or scheduled
    const isImmediate = reason === 'billing_issue' || reason === 'violation';
    const finalEffectiveAt = isImmediate ? now : effectiveAt;

    // TODO: Store cancellation data in database
    const cancellationData = {
      reason,
      reason_codes: reason_codes || [],
      notes: notes || '',
      canceled_at: now.toISOString(),
      effective_at: finalEffectiveAt.toISOString(),
      source: 'user_request'
    };

    console.log('Processing cancellation:', cancellationData);

    // TODO: Send notification emails/SMS
    // This would typically call the backend notification service

    return res.status(200).json({
      success: true,
      effective_at: finalEffectiveAt.toISOString(),
      subscription_status: 'canceled',
      message: isImmediate 
        ? 'Subscription canceled immediately' 
        : `Cancellation scheduled for ${finalEffectiveAt.toLocaleDateString()}`
    });

  } catch (error) {
    console.error('Error processing cancellation:', error);
    return res.status(500).json({ error: 'Internal server error' });
  }
}