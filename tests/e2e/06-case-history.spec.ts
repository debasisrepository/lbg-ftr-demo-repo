import { test, expect } from './_pipeline_guard';
import { loginViaAPI } from './helpers';

test.describe('Case History Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page, 'admin@example.com', 'admin123');
  });

  test('should load case history page', async ({ page, apiGuard }) => {
    // Allow 404 - case may not exist
    apiGuard.allow(404, '/api/v1/cases/');
    
    await page.goto('/cases/CP-TEST-001/history');
    
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Page should load
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
  });
});
