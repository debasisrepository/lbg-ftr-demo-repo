import { test, expect } from './_pipeline_guard';

test.describe('Colleague Case Retrieval', () => {
  test('colleague can access retrieval page after login', async ({ page }) => {
    // Login as colleague
    await page.goto('/login');
    
    // Change to colleague credentials
    await page.locator('input[name="username"], input[type="text"]').first().fill('colleague@example.com');
    await page.locator('input[name="password"], input[type="password"]').first().fill('colleague123');
    
    const submitButton = page.locator('button[type="submit"]').first();
    await submitButton.click();
    
    // Wait for login to complete
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 10000 });
    
    // Navigate to colleague retrieval
    await page.goto('/colleague/retrieve');
    await page.waitForLoadState('domcontentloaded');
    
    // Verify page loaded
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
    expect(page.url()).toContain('/colleague/retrieve');
  });
});
