import { test, expect } from './_pipeline_guard';
import { loginViaAPI } from './helpers';

test.describe('Case List Page', () => {
  test('should display case list page after login', async ({ page }) => {
    // Use full login flow to ensure auth works
    await page.goto('/login');
    
    // Login credentials are pre-filled
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Wait for login to complete
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
    
    // Navigate to cases
    await page.goto('/cases');
    await page.waitForLoadState('domcontentloaded');
    
    // Verify page loaded
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
    expect(page.url()).toContain('/cases');
  });
});
