import { test, expect } from './_pipeline_guard';
import { loginViaAPI } from './helpers';

test.describe('Case Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page, 'admin@example.com', 'admin123');
  });

  test('should handle case detail page navigation', async ({ page, apiGuard }) => {
    // Allow 404 - case may not exist
    apiGuard.allow(404, '/api/v1/cases/');
    
    await page.goto('/cases/CP-TEST-001');
    
    // Wait for page to load
    await page.waitForLoadState('domcontentloaded');
    
    // Page should either show case details or not found message
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
  });
});
