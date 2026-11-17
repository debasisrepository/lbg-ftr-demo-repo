import { test, expect } from './_pipeline_guard';

test.describe('Public Pages (No Auth Required)', () => {
  test('should display Service Status page without authentication', async ({ page }) => {
    await page.goto('/status');
    
    // Verify Service Status content is visible
    await expect(page.locator('h1, h2, h3').first()).toBeVisible({ timeout: 10000 });
    
    // Page should not redirect to login
    expect(page.url()).toContain('/status');
  });

  test('should display Lifeline page without authentication', async ({ page }) => {
    await page.goto('/lifeline');
    
    // Verify Lifeline content is visible - use first() to avoid strict mode violations
    await expect(page.locator('h1, h2, h3').first()).toBeVisible({ timeout: 10000 });
    
    // Page should not redirect to login
    expect(page.url()).toContain('/lifeline');
  });
});
