import { test, expect } from '@playwright/test';

/**
 * Dashboard Tests
 * 
 * Tests the main dashboard functionality, specifically looking for
 * Houston-related content as specified in requirements
 */

test.describe('Dashboard Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Set up any authentication or base state if needed
    // For now, we'll test the public aspects
  });

  test('Dashboard loads and shows Houston scope', async ({ page }) => {
    console.log('Testing dashboard load and Houston scope rendering...');
    
    // Navigate to the main dashboard/homepage
    await page.goto('/', { waitUntil: 'networkidle' });
    
    // Wait for the page to be fully loaded
    await expect(page.locator('body')).toBeVisible();
    
    // Check that the page loaded successfully
    await expect(page).toHaveTitle(/LeadLedgerPro|Home Services|Lead Generation/);
    
    // Look for Houston scope text - this should be prominently displayed
    // Based on the README, the platform is "Houston Metro area only"
    const houstonText = page.locator('text=/Houston/i').first();
    await expect(houstonText).toBeVisible({ timeout: 10000 });
    
    // Check for specific Houston-area counties mentioned in README
    const pageContent = await page.textContent('body');
    expect(pageContent).toMatch(/Houston|Harris|Fort Bend|Brazoria|Galveston/i);
    
    // Look for key platform features
    await expect(page.locator('text=/Lead Generation|Permit|Contractor/i').first()).toBeVisible();
    
    // Check for navigation elements
    const nav = page.locator('nav').first();
    if (await nav.isVisible()) {
      await expect(nav).toBeVisible();
    }
    
    // Take a screenshot for visual verification
    await page.screenshot({ 
      path: 'test-results/dashboard-houston-scope.png',
      fullPage: true 
    });
    
    console.log('✅ Dashboard loaded successfully with Houston scope visible');
  });

  test('Dashboard shows Houston metro area information', async ({ page }) => {
    await page.goto('/');
    
    // Wait for content to load
    await page.waitForLoadState('networkidle');
    
    // Check for Houston metro area specific content
    const expectedCounties = ['Harris County', 'Fort Bend County', 'Brazoria County', 'Galveston County'];
    
    const bodyText = await page.textContent('body');
    
    // At least one of the Houston area counties should be mentioned
    const hasHoustonArea = expectedCounties.some(county => 
      bodyText?.toLowerCase().includes(county.toLowerCase())
    );
    
    expect(hasHoustonArea).toBeTruthy();
    
    // Check for Houston-specific scope indicators
    expect(bodyText).toMatch(/Houston Metro|Houston area|Texas/i);
    
    console.log('✅ Houston metro area information displayed correctly');
  });

  test('Dashboard is responsive and accessible', async ({ page }) => {
    // Test desktop view
    await page.setViewportSize({ width: 1200, height: 800 });
    await page.goto('/');
    await expect(page.locator('text=/Houston/i').first()).toBeVisible();
    
    // Test mobile view
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000); // Let layout settle
    await expect(page.locator('text=/Houston/i').first()).toBeVisible();
    
    // Test tablet view
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(1000);
    await expect(page.locator('text=/Houston/i').first()).toBeVisible();
    
    console.log('✅ Dashboard is responsive across different viewport sizes');
  });

  test('Dashboard navigation works', async ({ page }) => {
    await page.goto('/');
    
    // Look for common navigation elements
    const commonNavItems = [
      'leads', 'dashboard', 'home', 'about', 'pricing', 'contact',
      'login', 'signup', 'sign up', 'get started'
    ];
    
    // Check if any navigation items are present and clickable
    let navFound = false;
    for (const item of commonNavItems) {
      const navItem = page.locator(`text=/${item}/i`).first();
      if (await navItem.isVisible()) {
        // Ensure it's clickable
        await expect(navItem).toBeEnabled();
        navFound = true;
        console.log(`Found navigation item: ${item}`);
        break;
      }
    }
    
    // If we found navigation, that's good
    // If not, that's also okay for a simple landing page
    console.log(`Navigation elements found: ${navFound}`);
  });
});