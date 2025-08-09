import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface CancelSubscriptionRequest {
  reason: string;
  notes?: string;
  effective_at: 'immediately' | 'end_of_period';
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Get user from auth header
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Missing or invalid authorization header' });
    }

    const token = authHeader.split(' ')[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    
    if (authError || !user) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    const cancelData: CancelSubscriptionRequest = req.body;
    
    // Validate required fields
    if (!cancelData.reason || !cancelData.effective_at) {
      return res.status(400).json({ error: 'reason and effective_at are required' });
    }

    // Call backend analytics service
    try {
      const analyticsResponse = await fetch(`${process.env.BACKEND_API_URL}/api/subscription/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          account_id: user.id,
          reason: cancelData.reason,
          notes: cancelData.notes || '',
          effective_at: cancelData.effective_at,
          plan: 'basic', // This should come from user's subscription data
          trial_or_paid: 'paid' // This should come from user's subscription data
        })
      });

      if (!analyticsResponse.ok) {
        console.error('Backend analytics tracking failed');
      }
    } catch (error) {
      console.error('Failed to call backend analytics:', error);
      // Don't fail the request if analytics fails
    }

    // Here you would typically:
    // 1. Update subscription status in your database
    // 2. Call payment provider (Stripe/etc) to cancel subscription
    // 3. Update user's access permissions
    
    // For now, we'll simulate the response
    const result = {
      id: `cancel_${Date.now()}`,
      account_id: user.id,
      status: 'canceled',
      effective_at: cancelData.effective_at,
      canceled_at: new Date().toISOString(),
      reason: cancelData.reason,
      notes: cancelData.notes
    };

    res.status(200).json({
      message: 'Subscription canceled successfully',
      data: result
    });

  } catch (error) {
    console.error('Cancel subscription error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}