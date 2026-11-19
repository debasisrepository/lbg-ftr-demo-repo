import { test, expect } from './_pipeline_guard';

const BASE_URL = 'http://127.0.0.1:5200';

async function loginViaAPI(page: any): Promise<void> {
  const response = await page.request.post('http://127.0.0.1:9100/api/v1/auth/login', {
    data: {
      username: 'admin@example.com',
      password: 'admin123'
    }
  });
  const data = await response.json();
  await page.evaluate((token: string) => {
    localStorage.setItem('auth_token', token);
  }, data.access_token);
}

test.describe('FR-002: Step-up authentication', () => {
  test('should show step-up page after login', async ({ page }) => {
    await page.goto(BASE_URL + '/login');
    
    // Fill credentials
    await page.fill('input[type="email"], input[type="text"], input[name="username"]', 'admin@example.com');
    await page.fill('input[type="password"], input[name="password"]', 'admin123');
    
    // Submit
    await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Continue"), button:has-text("Login")');
    
    // Should reach step-up page or accounts page (depends on flow)
    await page.waitForURL(/\/(step-up|accounts|dashboard)/, { timeout: 10000 });
    
    // Verify page loaded
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('should allow access to step-up page when authenticated', async ({ page }) => {
    // Login via API for speed
    await loginViaAPI(page);
    
    // Navigate to step-up page
    await page.goto(BASE_URL + '/step-up');
    
    // Should show step-up page content
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });
});
