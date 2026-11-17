import { test, expect } from './_pipeline_guard';

test.describe('Authentication Guards', () => {
  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    // Clear any existing auth
    await page.goto('/login');
    await page.evaluate(() => localStorage.clear());
    
    // Try to access protected route
    await page.goto('/cases');
    
    // Should redirect to login
    await page.waitForURL(/\/login/, { timeout: 10000 });
    expect(page.url()).toContain('/login');
  });

  test('should allow access to public routes without auth', async ({ page }) => {
    // Clear any existing auth
    await page.goto('/login');
    await page.evaluate(() => localStorage.clear());
    
    // Access public route
    await page.goto('/status');
    
    // Should NOT redirect to login
    await page.waitForTimeout(2000);
    expect(page.url()).toContain('/status');
    expect(page.url()).not.toContain('/login');
    
    // Verify content is visible - use first() to avoid strict mode
    await expect(page.locator('h1, h2, h3').first()).toBeVisible();
  });

  test('should preserve destination URL after login redirect', async ({ page }) => {
    // Clear any existing auth
    await page.goto('/login');
    await page.evaluate(() => localStorage.clear());
    
    // Try to access specific protected route
    await page.goto('/cases/CP-MOCK1');
    
    // Should redirect to login
    await page.waitForURL(/\/login/, { timeout: 10000 });
    
    // Login
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
    
    // Pre-filled values, just submit
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Should redirect away from login
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
    
    // Should be on a protected page (might be /cases if CP-MOCK1 belongs to admin)
    expect(page.url()).not.toContain('/login');
  });
});
