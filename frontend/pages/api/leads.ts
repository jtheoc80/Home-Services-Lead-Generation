import { NextApiRequest, NextApiResponse } from 'next';
import yaml from 'js-yaml';
import fs from 'fs';
import path from 'path';

// Note: Supabase client would be initialized here in production
// const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
// const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
// const supabase = createClient(supabaseUrl, supabaseKey);

interface LeadsQuery {
  region?: string;
  metro?: string;
  jurisdiction?: string;
  trade_tags?: string[];
  min_score?: number;
  limit?: number;
  offset?: number;
  sort?: 'score' | 'date' | 'value';
  order?: 'asc' | 'desc';
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method === 'GET') {
    return handleGetLeads(req, res);
  } else {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }
}

async function handleGetLeads(req: NextApiRequest, res: NextApiResponse) {
  try {
    // For demo purposes, return mock data when database is not available
    // In production, this would query the actual database
    
    // Parse query parameters
    const query: LeadsQuery = {
      region: req.query.region as string,
      metro: req.query.metro as string, 
      jurisdiction: req.query.jurisdiction as string,
      trade_tags: req.query.trade_tags ? 
        (Array.isArray(req.query.trade_tags) ? req.query.trade_tags : [req.query.trade_tags]) : undefined,
      min_score: req.query.min_score ? parseFloat(req.query.min_score as string) : undefined,
      limit: req.query.limit ? parseInt(req.query.limit as string) : 50,
      offset: req.query.offset ? parseInt(req.query.offset as string) : 0,
      sort: ['score', 'date', 'value'].includes(req.query.sort as string) ? 
        (req.query.sort as 'score' | 'date' | 'value') : 'score',
      order: ['asc', 'desc'].includes(req.query.order as string) ? 
        (req.query.order as 'asc' | 'desc') : 'desc'
    };

    // Load regions configuration to get jurisdiction mapping
    const configPath = path.join(process.cwd(), '..', 'config', 'regions.yaml');
    let jurisdictions: string[] = [];
    
    if (fs.existsSync(configPath)) {
      const configFile = fs.readFileSync(configPath, 'utf8');
      const config = yaml.load(configFile) as any;
      
      if (query.region && query.metro) {
        const regionData = config.regions?.[query.region];
        const metroData = regionData?.metros?.[query.metro];
        jurisdictions = metroData?.jurisdictions || [];
      }
    }

    // Return mock leads data for demonstration
    const mockLeads = [
      {
        id: 1,
        jurisdiction: "City of Houston",
        permit_id: "BP2025000128",
        address: "2468 Cedar Ln, Houston, TX 77006",
        description: "Kitchen renovation with new cabinets and appliances",
        work_class: "Residential Alteration",
        category: "residential",
        status: "Issued",
        issue_date: "2025-01-08",
        applicant: "ABC Contractors",
        owner: "John Smith",
        value: 25000,
        is_residential: true,
        latitude: 29.7604,
        longitude: -95.3698,
        trade_tags: ["kitchen"],
        budget_band: "$15-50k",
        lead_score: 87,
        created_at: "2025-01-08T10:00:00Z"
      },
      {
        id: 2,
        jurisdiction: "Harris County",
        permit_id: "HP2025000089",
        address: "1234 Oak Ave, Houston, TX 77002",
        description: "Roof replacement - asphalt shingles",
        work_class: "Residential Repair",
        category: "residential", 
        status: "Issued",
        issue_date: "2025-01-07",
        applicant: "Roofing Pro LLC",
        owner: "Jane Doe",
        value: 15000,
        is_residential: true,
        latitude: 29.7504,
        longitude: -95.3598,
        trade_tags: ["roofing"],
        budget_band: "$5-15k",
        lead_score: 92,
        created_at: "2025-01-07T14:30:00Z"
      }
    ];

    // Filter mock data based on query
    let filteredLeads = mockLeads;
    
    if (query.jurisdiction) {
      filteredLeads = filteredLeads.filter(lead => lead.jurisdiction === query.jurisdiction);
    } else if (jurisdictions.length > 0) {
      filteredLeads = filteredLeads.filter(lead => jurisdictions.includes(lead.jurisdiction));
    }
    
    if (query.trade_tags && query.trade_tags.length > 0) {
      filteredLeads = filteredLeads.filter(lead => 
        lead.trade_tags.some(tag => query.trade_tags!.includes(tag))
      );
    }
    
    if (query.min_score !== undefined) {
      filteredLeads = filteredLeads.filter(lead => lead.lead_score >= query.min_score!);
    }

    // Format response
    const response = {
      leads: filteredLeads.slice(query.offset!, query.offset! + query.limit!),
      pagination: {
        total: filteredLeads.length,
        limit: query.limit,
        offset: query.offset,
        has_more: (query.offset! + query.limit!) < filteredLeads.length
      },
      filters: {
        region: query.region,
        metro: query.metro,
        jurisdiction: query.jurisdiction,
        trade_tags: query.trade_tags,
        min_score: query.min_score,
        jurisdictions_included: jurisdictions
      },
      sorting: {
        sort: query.sort,
        order: query.order
      },
      note: "Demo data - replace with actual database query in production"
    };

    res.status(200).json(response);
  } catch (error) {
    console.error('Get leads error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
}