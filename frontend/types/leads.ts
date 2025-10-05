/**
 * Lead-related TypeScript types for frontend
 * Generated after swapping from permits to leads table
 */

// Base lead interface matching the database schema
export interface Lead {
  id: string;
  created_at: string;
  updated_at?: string;
  source?: string | null;
  name?: string | null;
  contractor_name?: string | null;
  owner_name?: string | null;
  lead_type?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  zipcode?: string | null;
  status?: string | null;
  service?: string | null; // Maps to permit_type in permits context
  trade?: string | null;
  county?: string | null;
  metadata?: any; // JSONB field
  // Enhanced fields for dashboard
  lead_score?: number | null;
  score_label?: string | null;
  value?: number | null;
  permit_id?: string | null;
  external_permit_id?: string | null;
  county_population?: number | null;
  user_id?: string | null;
}

// Lead interface with field mapping for permits-like display
export interface LeadForPermitsView {
  id: string;
  city: string | null; // maps to jurisdiction
  county: string | null;
  service: string | null; // maps to permit_type
  value: number | null;
  status: string | null;
  created_at: string; // maps to issued_date
  address: string | null;
}

// Enhanced lead interface with computed fields for UI
export interface EnhancedLead extends Lead {
  score?: number;
  scoreBreakdown?: {
    recency: number;
    residential: number;
    value: number;
    workClass: number;
  };
  tradeType?: string;
  permitValue?: number;
  lastUpdated?: string;
  permitNumber?: string;
}

// Lead insert payload interface (excludes auto-generated fields)
export interface LeadInsert {
  source?: string | null;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  status?: string | null;
  service?: string | null;
  county?: string | null;
  lead_score?: number | null;
  score_label?: string | null;
  value?: number | null;
  permit_id?: string | null;
  county_population?: number | null;
  user_id?: string | null;
  metadata?: any;
}

// Lead update payload interface (all fields optional)
export interface LeadUpdate {
  source?: string | null;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  status?: string | null;
  service?: string | null;
  county?: string | null;
  lead_score?: number | null;
  score_label?: string | null;
  value?: number | null;
  permit_id?: string | null;
  county_population?: number | null;
  user_id?: string | null;
  metadata?: any;
}

// API response types
export interface LeadsApiResponse {
  data: Lead[] | null;
  error: string | null;
}

export interface LeadApiResponse {
  data: Lead | null;
  error: string | null;
}

// Form types for lead creation
export interface CreateLeadFormData {
  name: string;
  email: string;
  phone: string;
  source: string;
  address?: string;
  city?: string;
  state?: string;
  zip?: string;
  service?: string;
  county?: string;
}

// Action result types
export interface CreateLeadResult {
  success: boolean;
  error?: string;
  leadId?: string;
}

// Hook return types
export interface UseLeadsReturn {
  leads: Lead[] | null;
  error: string | null;
  loading: boolean;
}

export interface UseEnhancedLeadsReturn {
  leads: EnhancedLead[] | null;
  error: string | null;
  loading: boolean;
}
