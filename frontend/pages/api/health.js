import { getSupabase } from '../../lib/supabaseClient';
import { config } from '../../lib/config';

/**
 * @typedef {Object} HealthResponse
 * @property {string} status - Overall status
 * @property {number} uptime - Server uptime
 * @property {Object} supabase - Supabase client status
 * @property {boolean} supabase.initialized - Whether client initialized successfully
 * @property {string} supabase.message - Status message
 * @property {Object} backend - Backend health status
 * @property {string} backend.status - Backend status
 * @property {string} backend.message - Backend message
 * @property {string} [backend.db] - Database status
 * @property {number} [backend.latencyMs] - Response latency
 */

export default async function handler(req, res) {
  // Health check endpoint for Railway deployment monitoring
  // Returns status, uptime, supabase client init success, and backend health
  
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  /** @type {HealthResponse} */
  const health = {
    status: 'ok',
    uptime: process.uptime(),
    supabase: {
      initialized: false,
      message: ''
    },
    backend: {
      status: 'unknown',
      message: 'Not checked'
    }
  };

  // Test Supabase client initialization
  try {
    // Try to initialize Supabase client on server side
    const { createClient } = await import('@supabase/supabase-js');
    const supabaseUrl = config.supabaseUrl;
    const supabaseAnonKey = config.supabaseAnonKey;
    
    if (!supabaseUrl || !supabaseAnonKey) {
      health.supabase = {
        initialized: false,
        message: 'Missing NEXT_PUBLIC_SUPABASE_URL or NEXT_PUBLIC_SUPABASE_ANON_KEY'
      };
    } else {
      // Create client and test basic connectivity
      const supabase = createClient(supabaseUrl, supabaseAnonKey);
      
      // Test a simple operation that doesn't require authentication
      const { error } = await supabase.from('leads').select('id').limit(1);
      
      if (error && error.code !== 'PGRST116') { // PGRST116 is "not found" which is OK
        health.supabase = {
          initialized: false,
          message: `Supabase error: ${error.message}`
        };
      } else {
        health.supabase = {
          initialized: true,
          message: 'Client initialized successfully'
        };
      }
    }
  } catch (error) {
    health.supabase = {
      initialized: false,
      message: `Initialization failed: ${error.message}`
    };
  }

  // Proxy backend health check
  try {
    const backendUrl = config.apiBase;
    if (backendUrl) {
      const startTime = Date.now();
      const response = await fetch(`${backendUrl}/healthz`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        // Add timeout to prevent hanging
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });
      
      const latencyMs = Date.now() - startTime;
      
      if (response.ok) {
        const backendHealth = await response.json();
        health.backend = {
          status: 'ok',
          message: `Backend healthy (${latencyMs}ms)`,
          db: backendHealth.db,
          latencyMs
        };
      } else {
        health.backend = {
          status: 'error',
          message: `Backend returned ${response.status}`,
          latencyMs
        };
      }
    } else {
      health.backend = {
        status: 'error',
        message: 'Backend URL not configured (NEXT_PUBLIC_API_BASE missing)'
      };
    }
  } catch (error) {
    health.backend = {
      status: 'error',
      message: `Backend unreachable: ${error.message}`
    };
  }

  // Determine overall health status
  const isHealthy = health.supabase.initialized && health.backend.status === 'ok';
  
  return res.status(200).json({
    ...health,
    status: isHealthy ? 'ok' : 'degraded'
  });
}