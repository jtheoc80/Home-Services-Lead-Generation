/**
 * TypeScript interfaces for Supabase database tables
 */

/**
 * Lead interface matching the public.leads table columns
 * Based on the database schema from docs/supabase/0001_init.sql
 */
export interface Lead {
  id: number;
  created_at: string;
  source?: string | null;
  name?: string | null;
  phone?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  zip?: string | null;
  status?: string | null;
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

 * Ingest log interface for tracking lead processing stages
 */
export interface IngestLog {
  id: number;
  trace_id: string;
  stage: string;
  ok: boolean;
  details?: any;
  created_at: string;
}

/**
 * Ingest log insert payload interface
 */
export interface IngestLogInsert {
  trace_id: string;

  stage: string;
  ok: boolean;
  details?: any;
}