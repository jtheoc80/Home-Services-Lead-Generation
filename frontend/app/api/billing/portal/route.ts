import { NextResponse, NextRequest } from 'next/server';

// Make this route dynamic since it reads headers
export const dynamic = 'force-dynamic';

/**
 * Billing portal API proxy
 * Forwards portal session requests to backend
 */
export async function POST(request: NextRequest) {
  try {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    const backendUrl = `${apiBase}/api/billing/portal`;
    
    // Get authorization header
    const authHeader = request.headers.get('authorization');
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
      },
    });

    const data = await response.json();
    
    return NextResponse.json(data, { 
      status: response.status 
    });
    
  } catch (error) {
    console.error('Portal API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to create portal session' },
      { status: 500 }
    );
  }
}