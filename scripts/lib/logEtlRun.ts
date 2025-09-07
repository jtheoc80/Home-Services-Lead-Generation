import axios from 'axios';

/**
 * Interface for ETL run data
 */
export interface EtlRunData {
  source_system: string;
  fetched: number;
  parsed: number;
  upserted: number;
  errors: number;
  first_issue_date?: string; // ISO date string
  last_issue_date?: string;  // ISO date string
  status?: 'success' | 'error' | 'running';
  error_message?: string;
  duration_ms?: number;
}

/**
 * Interface for the ETL run response from Supabase
 */
export interface EtlRunResponse {
  id: number;
  source_system: string;
  run_timestamp: string;
  status: string;
  fetched: number;
  parsed: number;
  upserted: number;
  errors: number;
  first_issue_date?: string;
  last_issue_date?: string;
  error_message?: string;
  duration_ms?: number;
  created_at: string;
  updated_at: string;
}

/**
 * Log an ETL run to the etl_runs table via Supabase REST API
 * 
 * @param data ETL run data to log
 * @returns Promise resolving to the created ETL run record
 * @throws Error if environment variables are missing or request fails
 */
export async function logEtlRun(data: EtlRunData): Promise<EtlRunResponse> {
  // Validate required environment variables
  const supabaseUrl = process.env.SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl) {
    throw new Error('SUPABASE_URL environment variable is required');
  }

  if (!supabaseKey) {
    throw new Error('SUPABASE_SERVICE_ROLE_KEY environment variable is required');
  }

  // Prepare the payload
  const payload = {
    source_system: data.source_system,
    run_timestamp: new Date().toISOString(),
    status: data.status || 'success',
    fetched: data.fetched,
    parsed: data.parsed,
    upserted: data.upserted,
    errors: data.errors,
    first_issue_date: data.first_issue_date || null,
    last_issue_date: data.last_issue_date || null,
    error_message: data.error_message || null,
    duration_ms: data.duration_ms || null
  };

  try {
    const url = `${supabaseUrl}/rest/v1/etl_runs`;
    
    const response = await axios.post<EtlRunResponse[]>(url, payload, {
      headers: {
        'apikey': supabaseKey,
        'Authorization': `Bearer ${supabaseKey}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
      }
    });

    // Supabase returns an array with the created record
    if (!response.data || response.data.length === 0) {
      throw new Error('No data returned from etl_runs insert');
    }

    return response.data[0];
  } catch (error) {
    // Log error without exposing secrets
    if (axios.isAxiosError(error)) {
      const message = error.response?.data?.message || error.message;
      const status = error.response?.status;
      throw new Error(`Failed to log ETL run to Supabase: ${status ? `${status} ` : ''}${message}`);
    } else {
      throw new Error(`Failed to log ETL run: ${error instanceof Error ? error.message : String(error)}`);
    }
  }
}

/**
 * Log an error ETL run
 * 
 * @param source_system Source system identifier
 * @param error_message Error message
 * @param duration_ms Optional duration in milliseconds
 * @returns Promise resolving to the created ETL run record
 */
export async function logEtlError(
  source_system: string, 
  error_message: string, 
  duration_ms?: number
): Promise<EtlRunResponse> {
  return logEtlRun({
    source_system,
    fetched: 0,
    parsed: 0,
    upserted: 0,
    errors: 1,
    status: 'error',
    error_message,
    duration_ms
  });
}