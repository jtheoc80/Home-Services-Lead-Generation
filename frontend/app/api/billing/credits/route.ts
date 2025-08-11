import { NextResponse, NextRequest } from 'next/server';

/**
 * Credits API proxy - forwards requests to backend billing API
 * This ensures no Stripe secrets are exposed to the client
 */
export async function GET(request: NextRequest) {
  try {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    const backendUrl = `${apiBase}/api/billing/credits`;
    
    // Get authorization header from client request
    const authHeader = request.headers.get('authorization');
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    const data = await response.json();
    
    return NextResponse.json(data, { 
      status: response.status,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
      }
    });
    
  } catch (error) {
    console.error('Credits API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch credit balance' },
      { status: 500 }
    );
  }
}