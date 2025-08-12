import { test, expect } from '@playwright/test';

/**
 * Debug Endpoint Security Tests
 * 
 * Tests the security implementation of the /api/leads/trace/[id] endpoint
 * to ensure proper authentication via X-Debug-Key header
 */

test.describe('Debug Endpoint Security Tests', () => {
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:3000';
  const DEBUG_ENDPOINT = `${API_BASE}/api/leads/trace/test-trace-id`;
  const DEBUG_KEY = process.env.DEBUG_API_KEY || 'test-key';
  
  test.beforeAll(async () => {
    console.log(`Testing debug endpoint security against: ${DEBUG_ENDPOINT}`);
    console.log(`Using debug key: [REDACTED]`);
  });

  test('should return 401 when no X-Debug-Key header is provided', async ({ request }) => {
    console.log('Testing request without X-Debug-Key header...');
    
    const response = await request.get(DEBUG_ENDPOINT);
    expect(response.status()).toBe(401);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('error');
    expect(responseBody.error).toContain('X-Debug-Key header required');
    
    console.log('✅ Correctly rejected request without debug key');
  });

  test('should return 401 when incorrect X-Debug-Key header is provided', async ({ request }) => {
    console.log('Testing request with incorrect X-Debug-Key header...');
    
    const response = await request.get(DEBUG_ENDPOINT, {
      headers: {
        'X-Debug-Key': 'wrong-key'
      }
    });
    
    expect(response.status()).toBe(401);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('error');
    expect(responseBody.error).toContain('X-Debug-Key header required');
    
    console.log('✅ Correctly rejected request with wrong debug key');
  });

  test('should return 401 when empty X-Debug-Key header is provided', async ({ request }) => {
    console.log('Testing request with empty X-Debug-Key header...');
    
    const response = await request.get(DEBUG_ENDPOINT, {
      headers: {
        'X-Debug-Key': ''
      }
    });
    
    expect(response.status()).toBe(401);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('error');
    expect(responseBody.error).toContain('X-Debug-Key header required');
    
    console.log('✅ Correctly rejected request with empty debug key');
  });

  test('should accept request with correct X-Debug-Key header', async ({ request }) => {
    console.log('Testing request with correct X-Debug-Key header...');
    
    const response = await request.get(DEBUG_ENDPOINT, {
      headers: {
        'X-Debug-Key': DEBUG_KEY
      }
    });
    
    // Should not be 401 (unauthorized) 
    // Could be 200 (success), 400 (bad request for invalid trace ID), or 500 (server error)
    // but not 401 since auth should pass
    expect(response.status()).not.toBe(401);
    
    if (response.status() === 200) {
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('trace_id');
      console.log('✅ Successfully accessed debug endpoint with correct key');
    } else if (response.status() === 400) {
      // This is expected if the trace ID doesn't exist
      const responseBody = await response.json();
      expect(responseBody).toHaveProperty('error');
      console.log('✅ Authentication passed, but trace ID not found (expected)');
    } else if (response.status() === 500) {
      const responseBody = await response.json();
      if (responseBody.error === 'Debug endpoint not available') {
        console.log('✅ Server correctly reports DEBUG_API_KEY not configured');
      } else {
        console.log('✅ Authentication passed, server error unrelated to auth');
      }
    }
  });

  test('should not leak debug key in error responses', async ({ request }) => {
    console.log('Testing that debug keys are not leaked in responses...');
    
    // Test with wrong key
    const response = await request.get(DEBUG_ENDPOINT, {
      headers: {
        'X-Debug-Key': 'definitely-wrong-key-that-might-leak'
      }
    });
    
    expect(response.status()).toBe(401);
    
    const responseBody = await response.json();
    const responseText = JSON.stringify(responseBody);
    
    // Ensure the wrong key is not leaked in the response
    expect(responseText).not.toContain('definitely-wrong-key-that-might-leak');
    expect(responseText).not.toContain(DEBUG_KEY);
    
    console.log('✅ Debug keys are properly masked in error responses');
  });

  test('should handle special characters in debug key header', async ({ request }) => {
    console.log('Testing request with special characters in X-Debug-Key header...');
    
    const specialCharKey = 'key<script>alert("xss")</script>';
    const response = await request.get(DEBUG_ENDPOINT, {
      headers: {
        'X-Debug-Key': specialCharKey
      }
    });
    
    expect(response.status()).toBe(401);
    
    const responseBody = await response.json();
    const responseText = JSON.stringify(responseBody);
    
    // Ensure special characters don't cause issues and aren't reflected
    expect(responseText).not.toContain('<script>');
    expect(responseText).not.toContain('alert');
    
    console.log('✅ Special characters in debug key handled safely');
  });

  test('should handle very long debug key header', async ({ request }) => {
    console.log('Testing request with very long X-Debug-Key header...');
    
    const longKey = 'a'.repeat(10000); // Very long key
    const response = await request.get(DEBUG_ENDPOINT, {
      headers: {
        'X-Debug-Key': longKey
      }
    });
    
    expect(response.status()).toBe(401);
    
    const responseBody = await response.json();
    expect(responseBody).toHaveProperty('error');
    
    console.log('✅ Very long debug key handled properly');
  });
});