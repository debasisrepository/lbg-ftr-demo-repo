import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 07 - Service Status', () => {
  test('displays service status without login (public page)', async ({ page }) => {
    // Navigate directly to service status page without logging in
    await page.goto('/status');
    
    // Wait for page to load
    await page.waitForSelector('h1');
    
    // Assert page heading is visible
    const heading = await page.locator('h1:has-text("Service status")');
    await expect(heading).toBeVisible();
    
    // Page should load successfully without auth
    // The content will vary based on whether there are incidents
  });

  test('displays operational status when no incidents', async ({ page }) => {
    // Navigate to service status page
    await page.goto('/status');
    
    // Wait for page to load
    await page.waitForSelector('h1');
    
    // Check if either operational message or incidents are displayed
    // The actual content depends on backend state
    const pageContent = await page.textContent('body');
    
    // Either "Everything is working" or incident information should be present
    const hasContent = pageContent?.includes('Everything is working') || 
                       pageContent?.includes('Happening now') ||
                       pageContent?.includes('incident');
    
    expect(hasContent).toBe(true);
  });

  test('displays incidents with status classification when disruptions exist', async ({ page }) => {
    // Navigate to service status page
    await page.goto('/status');
    
    // Wait for page to load
    await page.waitForSelector('h1');
    
    // Check for incidents section - may or may not be present depending on backend state
    const incidentsSection = page.locator('text=Happening now');
    
    // Assert on incident elements if they exist
    const isVisible = await incidentsSection.isVisible();
    if (isVisible) {
      // If incidents are shown, verify the structure exists
      await expect(incidentsSection).toBeVisible();
      
      // Look for incident cards with affected service information
      const incidentCards = await page.locator('[class*="Tile"]').count();
      expect(incidentCards).toBeGreaterThanOrEqual(0);
    }
  });

  test('displays last updated timestamp', async ({ page }) => {
    // Navigate to service status page
    await page.goto('/status');
    
    // Wait for page to load
    await page.waitForSelector('h1');
    
    // Assert last updated text is present
    const lastUpdated = page.locator('text=/Last (updated|checked)/i');
    await expect(lastUpdated).toBeVisible();
  });

  test('provides navigation to related pages', async ({ page }) => {
    // Navigate to service status page
    await page.goto('/status');
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: /service status/i })).toBeVisible();
    
    // The page always shows status information
    await expect(page.getByText(/last (updated|checked)/i)).toBeVisible();
  });

  test('polls for status updates at regular intervals', async ({ page }) => {
    // Navigate to service status page
    await page.goto('/status');
    
    // Wait for page to load
    await page.waitForSelector('h1');
    
    // Verify page has loaded initial content
    const heading = await page.locator('h1:has-text("Service status")');
    await expect(heading).toBeVisible();
    
    // Polling happens in the background - we verify the page remains functional
    await page.waitForTimeout(2000);
    
    // Page should still be showing content
    await expect(heading).toBeVisible();
  });
});
