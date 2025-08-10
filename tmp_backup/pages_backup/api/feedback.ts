import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface FeedbackSubmission {
  lead_id: number;
  rating: 'no_answer' | 'bad_contact' | 'not_qualified' | 'quoted' | 'won';
  deal_band?: string;
  reason_codes?: string[];
  notes?: string;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    return handleSubmitFeedback(req, res);
  } else if (req.method === 'GET') {
    return handleGetFeedback(req, res);
  } else {
    res.setHeader('Allow', ['POST', 'GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleSubmitFeedback(req: NextApiRequest, res: NextApiResponse) {
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

    const feedback: FeedbackSubmission = req.body;
    
    // Validate required fields
    if (!feedback.lead_id || !feedback.rating) {
      return res.status(400).json({ error: 'lead_id and rating are required' });
    }

    // Validate rating enum
    const validRatings = ['no_answer', 'bad_contact', 'not_qualified', 'quoted', 'won'];
    if (!validRatings.includes(feedback.rating)) {
      return res.status(400).json({ error: 'Invalid rating value' });
    }

    // Insert feedback using upsert to handle duplicates
    const { data, error } = await supabase
      .from('lead_feedback')
      .upsert({
        account_id: user.id,
        lead_id: feedback.lead_id,
        rating: feedback.rating,
        deal_band: feedback.deal_band || null,
        reason_codes: feedback.reason_codes || [],
        notes: feedback.notes || null,
      }, {
        onConflict: 'account_id,lead_id'
      })
      .select()
      .single();

    if (error) {
      console.error('Database error:', error);
      return res.status(500).json({ error: 'Failed to save feedback' });
    }

    // Update lead outcomes for ML training
    await updateLeadOutcome(feedback.lead_id, feedback.rating);

    res.status(200).json({
      message: 'Feedback submitted successfully',
      data: data
    });
  } catch (error) {
    console.error('Submit feedback error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleGetFeedback(req: NextApiRequest, res: NextApiResponse) {
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

    const { lead_id } = req.query;

    let query = supabase
      .from('lead_feedback')
      .select('*')
      .eq('account_id', user.id)
      .order('created_at', { ascending: false });

    if (lead_id) {
      query = query.eq('lead_id', parseInt(lead_id as string));
    }

    const { data, error } = await query;

    if (error) {
      console.error('Database error:', error);
      return res.status(500).json({ error: 'Failed to retrieve feedback' });
    }

    res.status(200).json({
      data: data
    });
  } catch (error) {
    console.error('Get feedback error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function updateLeadOutcome(leadId: number, rating: string) {
  try {
    // Create binary label for ML training
    const winLabel = rating === 'quoted' || rating === 'won';
    
    await supabase
      .from('lead_outcomes')
      .upsert({
        lead_id: leadId,
        win_label: winLabel,
        updated_at: new Date().toISOString()
      }, {
        onConflict: 'lead_id'
      });
  } catch (error) {
    console.error('Error updating lead outcome:', error);
    // Don't throw here to avoid failing the main request
  }
}