import { test, expect, Page } from '@playwright/test';

/**
 * Preview Smoke Tests
 * 
 * Tests critical endpoints on Vercel preview deployments:
 * - Homepage (/)
 * - Health endpoint (/api/health)
 * - Protected page (/leads)
 * 
 * Takes screenshots and saves HTML dumps on failure
 */

const ENDPOINTS = [
  { 
    path: '/', 
    name: 'Homepage',
    expectedStatus: 200,
    type: 'page'
  },
  { 
    path: '/api/health', 
    name: 'Health API',
    expectedStatus: 200,
    type: 'api'
  },
  { 
    path: '/leads', 
    name: 'Leads Page (Protected)',
    expectedStatus: [200, 401, 403], // May redirect to login or show auth error
    type: 'page'
  }
];

async function saveHtmlDump(page: Page, testName: string) {
  try {
    const html = await page.content();
    const fs = await import('fs');
    const path = await import('path');
    
    const dumpsDir = path.join(process.cwd(), 'test-results', 'html-dumps');
    await fs.promises.mkdir(dumpsDir, { recursive: true });
    
    const filename = `${testName.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.html`;
    const filepath = path.join(dumpsDir, filename);
    
    await fs.promises.writeFile(filepath, html, 'utf-8');
    console.log(`HTML dump saved: ${filepath}`);
  } catch (error) {
    console.error(`Failed to save HTML dump for ${testName}:`, error);
  }
}

async function takeScreenshot(page: Page, testName: string) {
  try {
    const path = await import('path');
    const screenshotsDir = path.join(process.cwd(), 'test-results', 'screenshots');
    
    const filename = `${testName.replace(/[^a-zA-Z0-9]/g, '_')}_${Date.now()}.png`;
    const filepath = path.join(screenshotsDir, filename);
    
    await page.screenshot({ 
      path: filepath, 
      fullPage: true 
    });
    console.log(`Screenshot saved: ${filepath}`);
  } catch (error) {
    console.error(`Failed to take screenshot for ${testName}:`, error);
  }
}

test.describe('Preview Smoke Tests', () => {
  
  test.beforeAll(async () => {
    console.log(`Testing against base URL: ${process.env.BASE_URL || 'http://localhost:3000'}`);
  });

  for (const endpoint of ENDPOINTS) {
    test(`${endpoint.name} (${endpoint.path})`, async ({ page }) => {
      console.log(`Testing ${endpoint.name} at ${endpoint.path}`);
      
      let response;
      let pageError = false;
      
      try {
        if (endpoint.type === 'api') {
          // For API endpoints, use page.request for direct HTTP testing
          response = await page.request.get(endpoint.path);
          
          console.log(`API Response Status: ${response.status()}`);
          
          // Check if status is acceptable
          const expectedStatuses = Array.isArray(endpoint.expectedStatus) 
            ? endpoint.expectedStatus 
            : [endpoint.expectedStatus];
            
          expect(expectedStatuses).toContain(response.status());
          
          // Try to parse JSON for API endpoints
          try {
            const responseBody = await response.json();
            console.log(`API Response Body:`, JSON.stringify(responseBody, null, 2));
          } catch (jsonError) {
            console.log(`API Response (non-JSON):`, await response.text());
          }
          
        } else {
          // For page endpoints, navigate and check response
          response = await page.goto(endpoint.path, { 
            waitUntil: 'networkidle',
            timeout: 30000 
          });
          
          if (!response) {
            throw new Error(`Failed to get response for ${endpoint.path}`);
          }
          
          console.log(`Page Response Status: ${response.status()}`);
          
          // Take screenshot for visual verification
          await takeScreenshot(page, `${endpoint.name}_success`);
          
          // Check if status is acceptable
          const expectedStatuses = Array.isArray(endpoint.expectedStatus) 
            ? endpoint.expectedStatus 
            : [endpoint.expectedStatus];
            
          expect(expectedStatuses).toContain(response.status());
          
          // Additional checks for successful page loads
          if (response.status() === 200) {
            // Wait for page to be ready
            await expect(page.locator('body')).toBeVisible();
            
            // Check that we have some content
            const bodyText = await page.textContent('body');
            expect(bodyText?.trim().length).toBeGreaterThan(0);
          }
        }
        
      } catch (error) {
        pageError = true;
        console.error(`Error testing ${endpoint.name}:`, error);
        
        // Save debugging artifacts on failure
        if (endpoint.type === 'page') {
          await takeScreenshot(page, `${endpoint.name}_failure`);
          await saveHtmlDump(page, `${endpoint.name}_failure`);
        }
        
        // Re-throw to fail the test
        throw error;
      }
    });
  }
  
  test('Overall system health check', async ({ page }) => {
    console.log('Running overall system health check...');
    
    // Test that at least the health endpoint is working
    const healthResponse = await page.request.get('/api/health');
    
    if (healthResponse.status() !== 200) {
      console.error('Health check failed, testing basic connectivity...');
      
      // Try to load homepage as fallback
      const homepageResponse = await page.goto('/', { 
        waitUntil: 'networkidle',
        timeout: 30000 
      });
      
      expect(homepageResponse?.status()).toBe(200);
      await takeScreenshot(page, 'fallback_homepage_check');
    } else {
      const healthData = await healthResponse.json();
      console.log('Health check passed:', JSON.stringify(healthData, null, 2));
      
      // Expect at least frontend to be working
      expect(healthData.frontend || healthData.status).toBeTruthy();
    }
  });
});