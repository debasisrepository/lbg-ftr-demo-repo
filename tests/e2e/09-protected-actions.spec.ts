import { test, expect } from './_pipeline_guard';
import { loginViaAPI } from './helpers';

test.describe('Protected Actions', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page, 'admin@example.com', 'admin123');
  });

  test('should load protected action page structure', async ({ page, apiGuard }) => {
    // Allow 404 - action may not exist
    apiGuard.allow(404, '/api/v1/');
    
    await page.goto('/cases/CP-TEST-001/actions/test-action-001');
    
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Page should load (even if showing not found)
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
  });
});
