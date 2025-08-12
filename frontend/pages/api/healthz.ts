import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', ['GET']);
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Get backend URL from environment variables
    const backendUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    
    // Fetch health data from backend
    const response = await fetch(`${backendUrl}/healthz`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      // Add timeout for health checks
      signal: AbortSignal.timeout(3000),
    });

    if (!response.ok) {
      throw new Error(`Backend health check failed: ${response.status}`);
    }

    const healthData = await response.json();
    
    // Add frontend health info
    const frontendHealth = {
      ...healthData,
      frontend: 'connected',
      frontend_uptime: process.uptime(),
    };

    // Check for development mode Redis warnings
    if (process.env.NODE_ENV === 'development' && healthData.redis !== 'connected') {
      console.warn('Redis is not connected in development mode');
    }

    return res.status(200).json(frontendHealth);
  } catch (error) {
    console.error('Health check error:', error);
    
    // Return minimal health info if backend is down
    return res.status(503).json({
      status: 'degraded',
      frontend: 'connected',
      frontend_uptime: process.uptime(),
      db: 'unknown',
      db_rtt_ms: null,
      redis: 'unknown',
      redis_rtt_ms: null,
      error: 'Backend unavailable',
      ts: Math.floor(Date.now() / 1000),
    });
  }
}