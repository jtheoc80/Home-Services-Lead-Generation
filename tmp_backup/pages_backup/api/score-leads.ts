import { NextApiRequest, NextApiResponse } from 'next';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY!;
const supabase = createClient(supabaseUrl, supabaseKey);

interface Lead {
  id: number;
  source: string;
  address: string;
  project_type?: string;
  permit_value?: number;
  trade_tags?: string[];
  owner_kind?: string;
  budget_band?: string;
  year_built?: number;
  created_at: string;
}

interface ScoringRequest {
  lead_ids?: number[];
  leads?: Lead[];
  use_ml?: boolean;
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'POST') {
    return handleScoreLeads(req, res);
  } else {
    res.setHeader('Allow', ['POST']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleScoreLeads(req: NextApiRequest, res: NextApiResponse) {
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

    const request: ScoringRequest = req.body;
    
    // Check feature flag for ML vs rules-based scoring
    const useMl = request.use_ml ?? (process.env.ENABLE_ML_SCORING === 'true');
    
    let leads: Lead[] = [];
    
    if (request.lead_ids && request.lead_ids.length > 0) {
      // Fetch leads from database if only IDs provided
      // Note: This would need to integrate with your leads data source
      // For now, return error as we don't have access to the leads table
      return res.status(400).json({ 
        error: 'Lead data retrieval not implemented. Please provide full lead objects.' 
      });
    } else if (request.leads && request.leads.length > 0) {
      leads = request.leads;
    } else {
      return res.status(400).json({ error: 'Either lead_ids or leads array must be provided' });
    }

    let scoredLeads;
    
    if (useMl) {
      scoredLeads = await scoreLeadsWithML(leads);
    } else {
      scoredLeads = await scoreLeadsWithRules(leads);
    }

    // Store scored results in lead_outcomes table
    await storeLeadOutcomes(scoredLeads);

    res.status(200).json({
      message: 'Leads scored successfully',
      method: useMl ? 'ml' : 'rules',
      data: scoredLeads
    });
  } catch (error) {
    console.error('Score leads error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}

async function scoreLeadsWithML(leads: Lead[]) {
  console.log('Using ML scoring');
  
  try {
    // Prepare features for ML inference
    const mlLeads = leads.map(lead => ({
      id: lead.id,
      features: {
        estimated_deal_value: lead.permit_value || extractValueFromBudgetBand(lead.budget_band || ''),
        feedback_age_days: Math.floor((Date.now() - new Date(lead.created_at).getTime()) / (1000 * 60 * 60 * 24)),
        has_contact_issues: false, // Default since we don't have feedback yet
        has_qualification_issues: false,
        is_weekend_feedback: new Date(lead.created_at).getDay() >= 5,
        feedback_hour: new Date(lead.created_at).getHours()
      }
    }));

    // Call ML inference API
    const response = await fetch(`${process.env.NEXTAUTH_URL || 'http://localhost:3000'}/api/ml-inference`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ leads: mlLeads })
    });

    if (!response.ok) {
      throw new Error(`ML inference failed: ${response.statusText}`);
    }

    const mlResults = await response.json();
    
    if (mlResults.error) {
      throw new Error(mlResults.error);
    }

    // Transform ML results to scoring format
    return mlResults.data.predictions.map((prediction: any) => ({
      lead_id: prediction.lead_id,
      score: prediction.calibrated_score,
      method: 'ml',
      factors: {
        model_version: prediction.model_version,
        win_probability: prediction.win_probability,
        confidence: prediction.confidence,
        predicted_success: prediction.predicted_success
      }
    }));

  } catch (error) {
    console.error('ML scoring failed, falling back to rules-based:', error);
    // Fallback to rules-based scoring
    return scoreLeadsWithRules(leads);
  }
}

function extractValueFromBudgetBand(budgetBand: string): number {
  const bandValues: { [key: string]: number } = {
    '$0-5k': 2500,
    '$5-15k': 10000,
    '$15-50k': 32500,
    '$50k+': 75000
  };
  return bandValues[budgetBand] || 0;
}

async function scoreLeadsWithRules(leads: Lead[]) {
  console.log('Using rules-based scoring');
  
  return leads.map(lead => {
    let score = 0;
    const factors: any = {};
    
    // Recency scoring (max 25 points, 3x weight)
    const daysOld = Math.floor((Date.now() - new Date(lead.created_at).getTime()) / (1000 * 60 * 60 * 24));
    const recencyScore = Math.max(0, Math.min(25, 25 - daysOld));
    score += recencyScore * 3;
    factors.recency = { score: recencyScore, weight: 3, days_old: daysOld };
    
    // Trade match scoring (max 25 points, 2x weight)
    const tradeScores: { [key: string]: number } = {
      'roofing': 25,
      'kitchen': 24,
      'bath': 22,
      'pool': 20,
      'fence': 15,
      'windows': 18,
      'foundation': 22,
      'solar': 20,
      'hvac': 18,
      'electrical': 16,
      'plumbing': 16
    };
    
    let maxTradeScore = 0;
    if (lead.trade_tags && lead.trade_tags.length > 0) {
      maxTradeScore = Math.max(...lead.trade_tags.map(tag => tradeScores[tag] || 0));
    }
    score += maxTradeScore * 2;
    factors.trade_match = { score: maxTradeScore, weight: 2, tags: lead.trade_tags };
    
    // Project value scoring (max 25 points, 2x weight)
    let valueScore = 0;
    if (lead.permit_value) {
      if (lead.permit_value >= 50000) valueScore = 25;
      else if (lead.permit_value >= 15000) valueScore = 20;
      else if (lead.permit_value >= 5000) valueScore = 15;
      else valueScore = 10;
    } else if (lead.budget_band) {
      const bandScores: { [key: string]: number } = {
        '$50k+': 25,
        '$15-50k': 20,
        '$5-15k': 15,
        '$0-5k': 10
      };
      valueScore = bandScores[lead.budget_band] || 10;
    }
    score += valueScore * 2;
    factors.project_value = { score: valueScore, weight: 2, value: lead.permit_value, band: lead.budget_band };
    
    // Property age scoring (max 15 points, 1x weight)
    let ageScore = 0;
    if (lead.year_built) {
      const age = new Date().getFullYear() - lead.year_built;
      if (age >= 25) ageScore = 15;
      else if (age >= 15) ageScore = 12;
      else if (age >= 10) ageScore = 8;
      else ageScore = 5;
    }
    score += ageScore;
    factors.property_age = { score: ageScore, weight: 1, year_built: lead.year_built };
    
    // Owner type scoring (max 10 points, 1x weight)
    let ownerScore = 5; // default
    if (lead.owner_kind === 'individual') ownerScore = 10;
    else if (lead.owner_kind === 'llc') ownerScore = 7;
    score += ownerScore;
    factors.owner_type = { score: ownerScore, weight: 1, type: lead.owner_kind };
    
    // Cap at 100
    const finalScore = Math.min(100, Math.round(score));
    
    return {
      lead_id: lead.id,
      score: finalScore,
      method: 'rules',
      factors: factors
    };
  });
}

async function storeLeadOutcomes(scoredLeads: any[]) {
  try {
    const outcomes = scoredLeads.map(scored => ({
      lead_id: scored.lead_id,
      calibrated_score: scored.score,
      updated_at: new Date().toISOString()
    }));

    const { error } = await supabase
      .from('lead_outcomes')
      .upsert(outcomes, {
        onConflict: 'lead_id'
      });

    if (error) {
      console.error('Error storing lead outcomes:', error);
    }
  } catch (error) {
    console.error('Error in storeLeadOutcomes:', error);
  }
}