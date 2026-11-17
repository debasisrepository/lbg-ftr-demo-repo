import { test, expect } from './_pipeline_guard';

test.describe('Login Flow', () => {
  test('should login through the form with valid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Verify login page is displayed
    await expect(page.locator('h1, h2, h3').filter({ hasText: /login|sign in/i })).toBeVisible({ timeout: 10000 });
    
    // Fill in login form with admin credentials
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
    
    await usernameInput.fill('admin@example.com');
    await passwordInput.fill('admin123');
    
    // Submit the form
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Wait for navigation away from login page
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
    
    // Verify we're on a protected page (should be /cases or /)
    const currentUrl = page.url();
    expect(currentUrl).toMatch(/\/(cases|$)/);
    
    // Verify a protected page element is visible (e.g., case list heading or navigation)
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible({ timeout: 10000 });
  });

  test('should reject invalid credentials', async ({ page, apiGuard }) => {
    // Allow 401 for this test - we're testing failure
    apiGuard.allow(401, '/api/v1/auth/login');
    
    await page.goto('/login');
    
    const usernameInput = page.locator('input[name="username"], input[type="text"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
    
    await usernameInput.fill('admin@example.com');
    await passwordInput.fill('wrongpassword');
    
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Should stay on login page or show error
    await page.waitForTimeout(2000);
    
    // Either still on login or error message visible
    const isOnLogin = page.url().includes('/login');
    const hasError = await page.locator('text=/invalid|error|incorrect|failed/i').isVisible().catch(() => false);
    
    expect(isOnLogin || hasError).toBeTruthy();
  });
});
