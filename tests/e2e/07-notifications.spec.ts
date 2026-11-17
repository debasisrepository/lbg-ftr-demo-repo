import { test, expect } from './_pipeline_guard';

test.describe('Notifications Page', () => {
  test('should load notifications page after login', async ({ page }) => {
    // Use full login flow
    await page.goto('/login');
    
    // Login credentials are pre-filled
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Wait for login to complete
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
    
    // Navigate to notifications
    await page.goto('/notifications');
    await page.waitForLoadState('domcontentloaded');
    
    // Verify page loaded
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
    expect(page.url()).toContain('/notifications');
  });
});
