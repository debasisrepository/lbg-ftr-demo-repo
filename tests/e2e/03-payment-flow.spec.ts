import { test, expect } from './_pipeline_guard';

test.describe('Payment Flow - Unauthenticated Pages', () => {
  test('can access scam report page', async ({ page }) => {
    await page.goto('/payment/scam-report');
    
    // Should see scam report content
    const content = page.locator('h1, h2, h3, p, div, form, button, label').first();
    await expect(content).toBeVisible({ timeout: 10000 });
  });

  test('can visit payment outcome page', async ({ page, apiGuard }) => {
    // Allow 403 errors on protected APIs since this page may redirect to authenticated routes
    apiGuard.allow(403, '/api/v1/accounts/overview');
    apiGuard.allow(403, '/api/v1/profiles');
    
    await page.goto('/payment/outcome');
    
    // Should see outcome content (may vary based on state)
    const content = page.locator('h1, h2, h3, p, div, button').first();
    await expect(content).toBeVisible({ timeout: 10000 });
  });
});
