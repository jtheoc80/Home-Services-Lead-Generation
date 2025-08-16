/**
 * TypeScript interfaces for Supabase database tables
 */

/**
 * Lead interface matching the public.leads table columns
 * Based on the enhanced database schema with all required fields
 */
export interface Lead {
  id: string; // UUID
  created_at: string;
  updated_at?: string;
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
  metadata?: any; // JSONB field
  // Enhanced fields for dashboard
  lead_score?: number | null;
  score_label?: string | null;
  value?: number | null;
  permit_id?: string | null;
  county_population?: number | null;
  user_id?: string | null;
}

/**
 * Lead insert payload interface (excludes auto-generated fields)
 * Used for creating new leads via API
 */
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

/**
 * Lead update payload interface (all fields optional)
 * Used for updating existing leads via API
 */
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

/**

 * Ingest logs interface matching the public.ingest_logs table
 * Used for tracking lead processing pipeline stages
 */
export interface IngestLog {
  id: number;
  created_at: string;
  trace_id: string | null;
  stage: string;
  ok: boolean;
  details: any; // jsonb field
}

/**
 * Ingest log insert payload interface (excludes auto-generated fields)
 * Used for creating new ingest log entries
 */
export interface IngestLogInsert {
  trace_id?: string | null;
  stage: string;
  ok: boolean;
  details?: any;
}