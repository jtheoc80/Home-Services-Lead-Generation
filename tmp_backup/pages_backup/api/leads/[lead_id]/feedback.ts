import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface VoteFeedback {
  vote_type: 'up' | 'down';
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { lead_id } = req.query;

  if (!lead_id || Array.isArray(lead_id)) {
    return res.status(400).json({ error: 'Invalid lead_id parameter' });
  }

  const leadId = parseInt(lead_id as string);
  if (isNaN(leadId)) {
    return res.status(400).json({ error: 'lead_id must be a valid number' });
  }

  if (req.method === 'POST') {
    return handleSubmitVote(req, res, leadId);
  } else if (req.method === 'GET') {
    return handleGetVote(req, res, leadId);
  } else {
    res.setHeader('Allow', ['POST', 'GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleSubmitVote(req: NextApiRequest, res: NextApiResponse, leadId: number) {
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

    const feedback: VoteFeedback = req.body;
    
    // Validate required fields
    if (!feedback.vote_type || !['up', 'down'].includes(feedback.vote_type)) {
      return res.status(400).json({ error: 'vote_type must be "up" or "down"' });
    }

    // Check if user already has feedback for this lead
    const { data: existingFeedback, error: checkError } = await supabase
      .from('lead_quality_events')
      .select('*')
      .eq('account_id', user.id)
      .eq('lead_id', leadId)
      .single();

    if (checkError && checkError.code !== 'PGRST116') { // PGRST116 is "not found"
      console.error('Database error checking existing feedback:', checkError);
      return res.status(500).json({ error: 'Failed to check existing feedback' });
    }

    // If feedback exists, check if it's within 24 hours
    if (existingFeedback) {
      const feedbackAge = Date.now() - new Date(existingFeedback.updated_at).getTime();
      const twentyFourHours = 24 * 60 * 60 * 1000;
      
      if (feedbackAge > twentyFourHours) {
        return res.status(403).json({ 
          error: 'Cannot change feedback after 24 hours',
          existing_vote: existingFeedback.event_type === 'feedback_positive' ? 'up' : 'down',
          can_change: false
        });
      }
    }

    // Determine event type and weight
    const eventType = feedback.vote_type === 'up' ? 'feedback_positive' : 'feedback_negative';
    const weight = feedback.vote_type === 'up' ? 5 : -10;

    // Insert or update feedback
    const { data, error } = await supabase
      .from('lead_quality_events')
      .upsert({
        account_id: user.id,
        lead_id: leadId,
        event_type: eventType,
        weight: weight,
        updated_at: new Date().toISOString()
      }, {
        onConflict: 'account_id,lead_id'
      })
      .select()
      .single();

    if (error) {
      console.error('Database error:', error);
      return res.status(500).json({ error: 'Failed to save feedback' });
    }

    res.status(200).json({
      message: 'Feedback submitted successfully',
      vote_type: feedback.vote_type,
      can_change: true,
      data: data
    });
  } catch (error) {
    console.error('Submit vote error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function handleGetVote(req: NextApiRequest, res: NextApiResponse, leadId: number) {
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

    // Get existing feedback for this user and lead
    const { data: feedback, error } = await supabase
      .from('lead_quality_events')
      .select('*')
      .eq('account_id', user.id)
      .eq('lead_id', leadId)
      .single();

    if (error && error.code !== 'PGRST116') { // PGRST116 is "not found"
      console.error('Database error:', error);
      return res.status(500).json({ error: 'Failed to retrieve feedback' });
    }

    let voteType = null;
    let canChange = false;

    if (feedback) {
      voteType = feedback.event_type === 'feedback_positive' ? 'up' : 'down';
      
      // Check if within 24 hours
      const feedbackAge = Date.now() - new Date(feedback.updated_at).getTime();
      const twentyFourHours = 24 * 60 * 60 * 1000;
      canChange = feedbackAge <= twentyFourHours;
    }

    res.status(200).json({
      vote_type: voteType,
      can_change: canChange,
      feedback_date: feedback?.updated_at || null
    });
  } catch (error) {
    console.error('Get vote error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}