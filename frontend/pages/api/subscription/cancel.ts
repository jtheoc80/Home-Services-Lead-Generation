import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface CancellationRequest {
  reason: string;
  notes?: string;
}

/**
 * Reason-to-weight mapping for cancellation impact on lead quality scores.
 * 
 * Weight guidelines:
 * - low_quality: -15 (strong negative signal about lead quality)
 * - out_of_area: -5 (user-specific, mild negative signal)
 * - too_expensive: -2 (mild negative, pricing issue)
 * - poor_support: -3 (service issue, not lead quality)
 * - found_alternative: -1 (neutral, competitive issue)
 * - other: -1 (minimal impact for unspecified reasons)
 */
const REASON_TO_WEIGHT: { [key: string]: number } = {
  'low_quality': -15,
  'out_of_area': -5,
  'too_expensive': -2,
  'poor_support': -3,
  'found_alternative': -1,
  'other': -1
};

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

    const cancellation: CancellationRequest = req.body;
    
    // Validate required fields
    if (!cancellation.reason) {
      return res.status(400).json({ error: 'Cancellation reason is required' });
    }

    // Get weight for the reason
    const weight = REASON_TO_WEIGHT[cancellation.reason] || REASON_TO_WEIGHT['other'];

    // Fetch all leads unlocked by this user in the last 30 days
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    // Query for leads accessed by this user in the last 30 days
    // Note: This assumes there's a way to track lead access/unlock events
    // For now, we'll use feedback submissions as a proxy for "unlocked" leads
    const { data: recentLeads, error: leadsError } = await supabase
      .from('lead_feedback')
      .select('lead_id')
      .eq('account_id', user.id)
      .gte('created_at', thirtyDaysAgo.toISOString());

    if (leadsError) {
      console.error('Error fetching user leads:', leadsError);
      return res.status(500).json({ error: 'Failed to fetch user leads' });
    }

    const affectedLeadIds = recentLeads?.map(row => row.lead_id) || [];

    // Insert cancellation record
    const { data: cancellationData, error: cancellationError } = await supabase
      .from('cancellations')
      .insert({
        account_id: user.id,
        reason: cancellation.reason,
        weight: weight,
        affected_leads: affectedLeadIds,
        notes: cancellation.notes || null
      })
      .select()
      .single();

    if (cancellationError) {
      console.error('Error saving cancellation:', cancellationError);
      return res.status(500).json({ error: 'Failed to save cancellation' });
    }

    // Insert lead quality events for each affected lead
    if (affectedLeadIds.length > 0) {
      const qualityEvents = affectedLeadIds.map(leadId => ({
        lead_id: leadId,
        account_id: user.id,
        event_type: 'cancellation',
        weight: weight,
        reason_code: cancellation.reason,
        metadata: {
          cancellation_id: cancellationData.id,
          notes: cancellation.notes
        }
      }));

      const { error: eventsError } = await supabase
        .from('lead_quality_events')
        .insert(qualityEvents);

      if (eventsError) {
        console.error('Error saving quality events:', eventsError);
        // Don't fail the request, but log the error
      }
    }

    res.status(200).json({
      message: 'Cancellation processed successfully',
      data: {
        cancellation_id: cancellationData.id,
        reason: cancellation.reason,
        weight: weight,
        affected_leads_count: affectedLeadIds.length,
        affected_leads: affectedLeadIds
      }
    });

  } catch (error) {
    console.error('Cancellation processing error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}