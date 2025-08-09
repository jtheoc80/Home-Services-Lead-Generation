import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface ReactivateSubscriptionRequest {
  plan: string;
  payment_provider: 'stripe' | 'crypto';
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

    const reactivateData: ReactivateSubscriptionRequest = req.body;
    
    // Validate required fields
    if (!reactivateData.plan || !reactivateData.payment_provider) {
      return res.status(400).json({ error: 'plan and payment_provider are required' });
    }

    // Validate payment provider
    if (!['stripe', 'crypto'].includes(reactivateData.payment_provider)) {
      return res.status(400).json({ error: 'payment_provider must be stripe or crypto' });
    }

    // Call backend analytics service
    try {
      const analyticsResponse = await fetch(`${process.env.BACKEND_API_URL}/api/subscription/reactivate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          account_id: user.id,
          plan: reactivateData.plan,
          payment_provider: reactivateData.payment_provider
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
    // 1. Reactivate subscription with payment provider
    // 2. Update subscription status in your database
    // 3. Restore user's access permissions
    // 4. Send confirmation email
    
    // For now, we'll simulate the response
    const result = {
      id: `reactivate_${Date.now()}`,
      account_id: user.id,
      status: 'active',
      plan: reactivateData.plan,
      payment_provider: reactivateData.payment_provider,
      reactivated_at: new Date().toISOString(),
      next_billing_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString() // 30 days from now
    };

    res.status(200).json({
      message: 'Subscription reactivated successfully',
      data: result
    });

  } catch (error) {
    console.error('Reactivate subscription error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}