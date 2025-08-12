import { NextResponse, NextRequest } from 'next/server';

// Make this route dynamic since it reads headers
export const dynamic = 'force-dynamic';

/**
 * Credits checkout API proxy
 * Forwards credit pack checkout requests to backend
 */
export async function POST(request: NextRequest) {
  try {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
    const backendUrl = `${apiBase}/api/billing/checkout/credits`;
    
    // Get authorization header
    const authHeader = request.headers.get('authorization');
    const idempotencyKey = request.headers.get('idempotency-key');
    
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader && { 'Authorization': authHeader }),
        ...(idempotencyKey && { 'Idempotency-Key': idempotencyKey }),
      },
    });

    const data = await response.json();
    
    return NextResponse.json(data, { 
      status: response.status 
    });
    
  } catch (error) {
    console.error('Credits checkout API proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to create credits checkout' },
      { status: 500 }
    );
  }
}