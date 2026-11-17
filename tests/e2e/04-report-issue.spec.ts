import { test, expect } from './_pipeline_guard';

test.describe('Report Issue (Case Creation)', () => {
  test('should load report issue page after login', async ({ page }) => {
    // Use full login flow
    await page.goto('/login');
    
    // Login credentials are pre-filled
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Wait for login to complete
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
    
    // Navigate to report page
    await page.goto('/report');
    await page.waitForLoadState('domcontentloaded');
    
    // Should be on report page
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
    expect(page.url()).toContain('/report');
  });
});
