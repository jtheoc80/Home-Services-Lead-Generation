/**
 * Frontend API client for external backend services.
 * 
 * This module provides functions to interact with the external backend API
 * using the NEXT_PUBLIC_API_BASE environment variable.
 */

import { getExternalApiUrl } from './config';

export interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'unknown';
  timestamp: string;
  details?: string;
}

/**
 * Fetch health status from the external backend
 */
export async function fetchHealthStatus(): Promise<HealthStatus> {
  try {
    const url = getExternalApiUrl('/healthz');
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Don't cache health checks
      cache: 'no-store',
    });

    if (response.ok) {
      // Try to parse JSON response, but fallback to simple status
      try {
        const data = await response.json();
        return {
          status: 'healthy',
          timestamp: new Date().toISOString(),
          details: data.details || 'Backend is responding',
        };
      } catch {
        return {
          status: 'healthy',
          timestamp: new Date().toISOString(),
          details: 'Backend is responding',
        };
      }
    } else {
      return {
        status: 'unhealthy',
        timestamp: new Date().toISOString(),
        details: `HTTP ${response.status}: ${response.statusText}`,
      };
    }
  } catch (error) {
    return {
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      details: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}

/**
 * Generic function to make API calls to the external backend
 */
export async function apiCall<T = unknown>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = getExternalApiUrl(endpoint);
  
  const defaultOptions: RequestInit = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  const response = await fetch(url, {
    ...defaultOptions,
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API call failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}