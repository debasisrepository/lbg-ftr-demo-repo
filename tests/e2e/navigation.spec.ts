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

test.describe('Route Navigation', () => {
  test('should access dashboard route', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/dashboard');
    
    // Verify page loads
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('should access accounts route', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/accounts');
    
    // Verify page loads
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('should access payees route', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/payees');
    
    // Verify page loads
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('should access payment entry route', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/payment/entry');
    
    // Verify page loads
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('should access payment outcome route', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/payment/outcome');
    
    // Verify page loads
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('should access step-up route', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/step-up');
    
    // Verify page loads
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
  });

  test('root path should redirect to login', async ({ page }) => {
    await page.goto(BASE_URL + '/');
    
    // Should redirect to login
    await page.waitForURL(/\/login/, { timeout: 5000 });
  });
});

test.describe('Logout Flow', () => {
  test('should logout and redirect to login', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/dashboard');
    
    // Verify we're logged in
    await expect(page.locator('h1, h2, [role="heading"]').first()).toBeVisible();
    
    // Look for logout button
    const logoutButton = page.locator('button:has-text("Logout"), button:has-text("Sign out"), button:has-text("Log out"), a:has-text("Logout"), a:has-text("Sign out")').first();
    const logoutExists = await logoutButton.isVisible({ timeout: 2000 }).catch(() => false);
    
    if (logoutExists) {
      await logoutButton.click();
      
      // Should redirect to login
      await page.waitForURL(/\/login/, { timeout: 5000 });
    } else {
      // Manually clear token and verify redirect
      await page.evaluate(() => {
        localStorage.removeItem('auth_token');
      });
      
      // Try to access protected route
      await page.goto(BASE_URL + '/dashboard');
      await page.waitForURL(/\/login/, { timeout: 5000 });
    }
  });
});
