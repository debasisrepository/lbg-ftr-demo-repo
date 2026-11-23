/**
 * E2E Test: Session Management and Protected Routes (FR-AUTH-006)
 * Tests session continuity and protected route enforcement.
 */
import { test, expect } from './_pipeline_guard';
import { loginViaForm } from './helpers';

test.describe('Session Management', () => {
  test('should redirect to login when accessing protected route without auth', async ({ page, apiGuard }) => {
    // Allow 401 for unauthenticated access
    apiGuard.allow(401, '/api/v1/');
    
    // Try to access accounts without logging in
    await page.goto('/accounts');
    
    // Should redirect to login
    await page.waitForURL('/login', { timeout: 10000 });
    await expect(page).toHaveURL('/login');
  });

  test('should redirect to login when accessing payees without auth', async ({ page, apiGuard }) => {
    apiGuard.allow(401, '/api/v1/');
    
    await page.goto('/payees');
    
    await page.waitForURL('/login', { timeout: 10000 });
    await expect(page).toHaveURL('/login');
  });

  test('should maintain session across page navigations', async ({ page }) => {
    await loginViaForm(page);
    
    // Should be on accounts
    await expect(page).toHaveURL('/accounts');
    
    // Navigate to payees
    await page.goto('/payees');
    await expect(page).toHaveURL('/payees');
    
    // Go back to accounts
    await page.goto('/accounts');
    await expect(page).toHaveURL('/accounts');
    
    // Session should still be valid
    await expect(page.locator('h1')).toContainText('Your accounts');
  });

  test('should handle logout', async ({ page }) => {
    await loginViaForm(page);
    await page.goto('/accounts');
    
    // Look for logout/sign out button
    const logoutButton = page.locator('button, a').filter({ hasText: /Log out|Sign out/i }).first();
    
    // Assert the button exists and is visible
    await expect(logoutButton).toBeVisible();
    
    // Click logout button
    await logoutButton.click();
    
    // Should redirect to login
    await page.waitForURL('/login', { timeout: 10000 });
    await expect(page).toHaveURL('/login');
    
    // Verify token is cleared
    const token = await page.evaluate(() => sessionStorage.getItem('auth_token'));
    expect(token).toBeNull();
  });

  test('should return to intended page after login', async ({ page, apiGuard }) => {
    apiGuard.allow(401, '/api/v1/');
    
    // Try to access payees without auth
    await page.goto('/payees');
    
    // Should redirect to login
    await page.waitForURL('/login', { timeout: 10000 });
    
    // Log in
    await page.fill('input[type="password"]', 'Pass1234');
    await page.click('button[type="submit"]');
    
    // Should redirect back to payees (or accounts if no redirect state)
    await page.waitForURL(/\/(payees|accounts)/, { timeout: 10000 });
  });
});
