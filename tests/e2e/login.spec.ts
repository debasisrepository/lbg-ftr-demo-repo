import { test, expect } from './_pipeline_guard';

const BASE_URL = 'http://127.0.0.1:5200';

test.describe('FR-001: Sign in', () => {
  test('should complete sign in with valid credentials through the form', async ({ page }) => {
    // This test MUST use the form (not API shortcuts) per pipeline requirement
    await page.goto(BASE_URL + '/login');
    
    // Wait for page to load
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
    
    // Fill in the login form
    await page.fill('input[type="email"], input[type="text"], input[name="username"]', 'admin@example.com');
    await page.fill('input[type="password"], input[name="password"]', 'admin123');
    
    // Submit the form
    await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Continue"), button:has-text("Login")');
    
    // Verify we left the login page and reached a protected page
    await page.waitForURL(/\/(dashboard|step-up|accounts)/, { timeout: 10000 });
    
    // Verify a protected page element is visible
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('should show validation error when username field is empty', async ({ page }) => {
    await page.goto(BASE_URL + '/login');
    
    // Fill only password
    await page.fill('input[type="password"], input[name="password"]', 'admin123');
    
    // Submit the form
    await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Continue"), button:has-text("Login")');
    
    // Should show validation error and stay on login page
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('text=/required|cannot be empty|please enter/i').first()).toBeVisible({ timeout: 2000 });
  });

  test('should show validation error when password field is empty', async ({ page }) => {
    await page.goto(BASE_URL + '/login');
    
    // Fill only username
    await page.fill('input[type="email"], input[type="text"], input[name="username"]', 'admin@example.com');
    
    // Submit the form
    await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Continue"), button:has-text("Login")');
    
    // Should show validation error and stay on login page
    await expect(page).toHaveURL(/\/login/);
    await expect(page.locator('text=/required|cannot be empty|please enter/i').first()).toBeVisible({ timeout: 2000 });
  });

  test('should show generic error for invalid credentials', async ({ page, apiGuard }) => {
    // Wrong credentials should return 401 - this is expected
    apiGuard.allow(401, '/auth/login');
    
    await page.goto(BASE_URL + '/login');
    
    // Fill with incorrect credentials
    await page.fill('input[type="email"], input[type="text"], input[name="username"]', 'admin@example.com');
    await page.fill('input[type="password"], input[name="password"]', 'wrongpassword');
    
    // Submit the form
    await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Continue"), button:has-text("Login")');
    
    // Should show generic error message (not revealing which field was wrong)
    await expect(page.locator('text=/invalid|incorrect|authentication failed|sign.?in failed/i').first()).toBeVisible({ timeout: 2000 });
    
    // Should still be on login page
    await expect(page).toHaveURL(/\/login/);
  });
});
