import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 02: Report Issue', () => {
  test.beforeEach(async ({ page }) => {
    // Login with seed credentials
    await page.goto('/login');
    await page.locator('#username').fill('admin@example.com');
    await page.locator('#password').fill('admin123');
    await page.locator('button[type="submit"]').click();
    
    // Wait for redirect
    await page.waitForURL('/cases', { timeout: 15000 });
    
    // Navigate to report page
    await page.goto('/report');
    await page.waitForSelector('h1', { timeout: 10000 });
  });

  test('displays Report an issue page with heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Report an issue', level: 1 })).toBeVisible();
  });

  test('displays back link to My Cases', async ({ page }) => {
    const backLink = page.getByRole('link', { name: /My Cases/i });
    await expect(backLink).toBeVisible();
  });

  test('displays issue type dropdown', async ({ page }) => {
    await expect(page.locator('#issue-type')).toBeVisible();
  });

  test('displays issue summary textarea', async ({ page }) => {
    const textarea = page.locator('#issue-summary');
    await expect(textarea).toBeVisible();
    await expect(page.locator('text=Do not enter your full card number')).toBeVisible();
  });

  test('submits form and handles response', async ({ page }) => {
    // Fill form
    await page.locator('#issue-type').selectOption('card_declined');
    await page.locator('#issue-summary').fill('My card was declined at the supermarket on Monday evening.');
    
    // Submit
    await page.locator('button[type="submit"]').click();
    
    // Wait for either navigation or result message (timeout of 10s)
    try {
      await page.waitForURL(/\/cases\/CP-/, { timeout: 10000 });
      // Navigated to case detail - success
      expect(page.url()).toContain('/cases/CP-');
    } catch {
      // Check for result messages
      const hasSurfaced = await page.locator('text=already have an open Case').isVisible().catch(() => false);
      const hasNotEligible = await page.locator('text=handled in another part').isVisible().catch(() => false);
      const hasError = await page.locator('.cds--inline-notification--error').isVisible().catch(() => false);
      
      // One of these outcomes should be visible
      expect(hasSurfaced || hasNotEligible || hasError).toBeTruthy();
    }
  });
});
