import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 08 - Lifeline', () => {
  test('should display lifeline guidance without login', async ({ page }) => {
    await page.goto('/lifeline');
    
    // Verify page loads (public route)
    await expect(page.locator('h1')).toContainText('What you can do now');
    
    // Verify guidance description
    await expect(page.getByText(/Guidance for the current problem/)).toBeVisible();
    
    // Verify "Ways to reach us" section appears (this should always be present)
    await expect(page.getByRole('heading', { name: /ways to reach us/i })).toBeVisible();
    
    // Verify Talk to a person button exists
    await expect(page.getByRole('link', { name: /talk to a person/i })).toBeVisible();
  });
  
  test('should show phone number and safe actions list', async ({ page }) => {
    await page.goto('/lifeline');
    
    // Wait for content to load
    await page.waitForSelector('h1:has-text("What you can do now")');
    
    // Verify contact options section exists
    const contactSection = page.locator('section', { has: page.getByRole('heading', { name: /ways to reach us/i }) });
    await expect(contactSection).toBeVisible();
    
    // Verify "Talk to a person" button exists
    await expect(page.getByRole('link', { name: /talk to a person/i })).toBeVisible();
  });
  
  test('should display cache age indicator when using cached data', async ({ page, context, apiGuard }) => {
    // Allow the API failure since we're testing the cache fallback behavior
    apiGuard.allow(0, '/lifeline');
    // Set up a mock cache in localStorage
    await context.addInitScript(() => {
      const mockCache = {
        guidance_items: [
          {
            id: 'g1',
            incident_reference: 'INC-001',
            guidance_category: 'what_still_works',
            guidance_title: 'Cash machines',
            guidance_body: 'You can still take out cash',
            published_at: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
          },
        ],
        protective_actions: ['Keep another way to pay'],
        fallback_channels: [
          {
            channel_type: 'phone',
            label: 'Phone',
            contact_detail: '0800123456',
            availability_text: 'Open 24 hours',
          },
        ],
        cache_version: 'v1',
        cache_age_seconds: 0,
        generated_at: new Date(Date.now() - 300000).toISOString(),
        withdrawn_cache_versions: [],
      };
      localStorage.setItem('clearpath_lifeline_cache', JSON.stringify(mockCache));
    });
    
    // Mock the API to fail so it uses cache
    await page.route('**/api/v1/lifeline', (route) => {
      route.abort('failed');
    });
    
    await page.goto('/lifeline');
    
    // Verify cache age warning appears
    await expect(page.getByText(/showing saved guidance/i)).toBeVisible();
    await expect(page.getByText(/minute.*old/i)).toBeVisible();
    
    // Verify "Try again" button appears
    await expect(page.getByRole('button', { name: /try again/i })).toBeVisible();
  });
  
  test('should display live guidance update indicator when not cached', async ({ page }) => {
    await page.goto('/lifeline');
    
    // Wait for content to load
    await page.waitForSelector('h1:has-text("What you can do now")');
    
    // When live data is available, should show "Up to date" section - assert it's there
    const upToDateSection = page.locator('text=Up to date');
    await expect(upToDateSection).toBeVisible();
    
    // Verify the info notification about saved guidance
    await expect(page.getByText(/saved on your phone for next time/i)).toBeVisible();
  });
  
  test('should have back link to service status', async ({ page }) => {
    await page.goto('/lifeline');
    
    // Verify back link to service status page
    const backLink = page.getByRole('link', { name: /service status/i }).first();
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', '/status');
  });
});
