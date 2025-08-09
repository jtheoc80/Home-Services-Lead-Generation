import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface LeadQualityIssue {
  lead_id: number;
  total_negative_weight: number;
  event_count: number;
  most_common_reason: string;
  jurisdiction: string;
  address: string;
  global_score: number;
}

interface JurisdictionScore {
  jurisdiction: string;
  trade: string;
  avg_score: number;
  lead_count: number;
  score_drop: number;
}

interface ReasonBreakdown {
  reason_code: string;
  event_count: number;
  total_weight: number;
  affected_leads: number;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Check for admin authorization
    const authHeader = req.headers.authorization;
    if (!authHeader?.startsWith('Bearer ')) {
      return res.status(401).json({ error: 'Missing or invalid authorization header' });
    }

    const token = authHeader.split(' ')[1];
    const { data: { user }, error: authError } = await supabase.auth.getUser(token);
    
    if (authError || !user) {
      return res.status(401).json({ error: 'Invalid token' });
    }

    // Check if user has admin role (this would need to be implemented in your auth system)
    // For now, we'll assume the endpoint is admin-only based on access control

    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    // 1. Get leads with most negative quality events in last 30 days
    const problemLeadsQuery = `
      SELECT 
        lqe.lead_id,
        SUM(lqe.weight) as total_negative_weight,
        COUNT(*) as event_count,
        MODE() WITHIN GROUP (ORDER BY lqe.reason_code) as most_common_reason,
        l.jurisdiction,
        l.address,
        l.global_score
      FROM lead_quality_events lqe
      JOIN leads l ON l.id = lqe.lead_id
      WHERE lqe.created_at >= $1
      AND lqe.weight < 0
      GROUP BY lqe.lead_id, l.jurisdiction, l.address, l.global_score
      ORDER BY total_negative_weight ASC
      LIMIT 50
    `;

    const { data: problemLeads, error: problemLeadsError } = await supabase
      .rpc('exec_raw_sql', {
        query: problemLeadsQuery,
        params: [thirtyDaysAgo.toISOString()]
      });

    if (problemLeadsError) {
      console.error('Error fetching problem leads:', problemLeadsError);
    }

    // 2. Get jurisdictions with largest score drops
    // Note: This is simplified since we don't have historical score tracking yet
    const jurisdictionScoresQuery = `
      SELECT 
        l.jurisdiction,
        unnest(l.trade_tags) as trade,
        AVG(l.global_score) as avg_score,
        COUNT(*) as lead_count,
        0 as score_drop
      FROM leads l
      WHERE l.global_score IS NOT NULL
      AND l.trade_tags IS NOT NULL
      GROUP BY l.jurisdiction, unnest(l.trade_tags)
      HAVING COUNT(*) >= 5
      ORDER BY avg_score ASC
      LIMIT 20
    `;

    const { data: jurisdictionScores, error: jurisdictionError } = await supabase
      .rpc('exec_raw_sql', {
        query: jurisdictionScoresQuery
      });

    if (jurisdictionError) {
      console.error('Error fetching jurisdiction scores:', jurisdictionError);
    }

    // 3. Get breakdown by reason code
    const reasonBreakdownQuery = `
      SELECT 
        reason_code,
        COUNT(*) as event_count,
        SUM(weight) as total_weight,
        COUNT(DISTINCT lead_id) as affected_leads
      FROM lead_quality_events
      WHERE created_at >= $1
      AND reason_code IS NOT NULL
      GROUP BY reason_code
      ORDER BY total_weight ASC
    `;

    const { data: reasonBreakdown, error: reasonError } = await supabase
      .rpc('exec_raw_sql', {
        query: reasonBreakdownQuery,
        params: [thirtyDaysAgo.toISOString()]
      });

    if (reasonError) {
      console.error('Error fetching reason breakdown:', reasonError);
    }

    // Fallback queries using standard Supabase API if RPC fails
    let fallbackProblemLeads = [];
    let fallbackJurisdictionScores = [];
    let fallbackReasonBreakdown = [];

    if (problemLeadsError) {
      // Get quality events and process client-side
      const { data: events } = await supabase
        .from('lead_quality_events')
        .select('lead_id, weight, reason_code, leads(jurisdiction, address, global_score)')
        .gte('created_at', thirtyDaysAgo.toISOString())
        .lt('weight', 0)
        .order('weight', { ascending: true });

      if (events) {
        const leadAggregates = events.reduce((acc, event) => {
          const leadId = event.lead_id;
          if (!acc[leadId]) {
            acc[leadId] = {
              lead_id: leadId,
              total_negative_weight: 0,
              event_count: 0,
              reasons: [],
              lead_data: event.leads
            };
          }
          acc[leadId].total_negative_weight += event.weight;
          acc[leadId].event_count += 1;
          if (event.reason_code) {
            acc[leadId].reasons.push(event.reason_code);
          }
          return acc;
        }, {});

        fallbackProblemLeads = Object.values(leadAggregates)
          .map((agg: any) => ({
            lead_id: agg.lead_id,
            total_negative_weight: agg.total_negative_weight,
            event_count: agg.event_count,
            most_common_reason: agg.reasons.length > 0 ? 
              agg.reasons.sort((a,b) => 
                agg.reasons.filter(v => v === a).length - agg.reasons.filter(v => v === b).length
              ).pop() : 'unknown',
            jurisdiction: agg.lead_data?.jurisdiction || 'unknown',
            address: agg.lead_data?.address || 'unknown',
            global_score: agg.lead_data?.global_score || 50
          }))
          .sort((a, b) => a.total_negative_weight - b.total_negative_weight)
          .slice(0, 50);
      }
    }

    if (jurisdictionError) {
      const { data: leads } = await supabase
        .from('leads')
        .select('jurisdiction, trade_tags, global_score')
        .not('global_score', 'is', null)
        .not('trade_tags', 'is', null);

      if (leads) {
        const jurisdictionAggregates = {};
        leads.forEach(lead => {
          if (lead.trade_tags) {
            lead.trade_tags.forEach(trade => {
              const key = `${lead.jurisdiction}:${trade}`;
              if (!jurisdictionAggregates[key]) {
                jurisdictionAggregates[key] = {
                  jurisdiction: lead.jurisdiction,
                  trade: trade,
                  scores: [],
                  lead_count: 0
                };
              }
              jurisdictionAggregates[key].scores.push(lead.global_score);
              jurisdictionAggregates[key].lead_count += 1;
            });
          }
        });

        fallbackJurisdictionScores = Object.values(jurisdictionAggregates)
          .filter((agg: any) => agg.lead_count >= 5)
          .map((agg: any) => ({
            jurisdiction: agg.jurisdiction,
            trade: agg.trade,
            avg_score: agg.scores.reduce((sum, score) => sum + score, 0) / agg.scores.length,
            lead_count: agg.lead_count,
            score_drop: 0
          }))
          .sort((a, b) => a.avg_score - b.avg_score)
          .slice(0, 20);
      }
    }

    if (reasonError) {
      const { data: events } = await supabase
        .from('lead_quality_events')
        .select('reason_code, weight, lead_id')
        .gte('created_at', thirtyDaysAgo.toISOString())
        .not('reason_code', 'is', null);

      if (events) {
        const reasonAggregates = events.reduce((acc, event) => {
          const reason = event.reason_code;
          if (!acc[reason]) {
            acc[reason] = {
              reason_code: reason,
              event_count: 0,
              total_weight: 0,
              lead_ids: new Set()
            };
          }
          acc[reason].event_count += 1;
          acc[reason].total_weight += event.weight;
          acc[reason].lead_ids.add(event.lead_id);
          return acc;
        }, {});

        fallbackReasonBreakdown = Object.values(reasonAggregates)
          .map((agg: any) => ({
            reason_code: agg.reason_code,
            event_count: agg.event_count,
            total_weight: agg.total_weight,
            affected_leads: agg.lead_ids.size
          }))
          .sort((a, b) => a.total_weight - b.total_weight);
      }
    }

    res.status(200).json({
      message: 'Lead quality analytics retrieved successfully',
      data: {
        problem_leads: problemLeads || fallbackProblemLeads,
        jurisdiction_scores: jurisdictionScores || fallbackJurisdictionScores,
        reason_breakdown: reasonBreakdown || fallbackReasonBreakdown,
        generated_at: new Date().toISOString(),
        period: '30 days'
      }
    });

  } catch (error) {
    console.error('Lead quality analytics error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}