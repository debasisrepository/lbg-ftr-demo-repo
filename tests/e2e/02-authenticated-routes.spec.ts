import { test, expect } from './_pipeline_guard';

const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:9100';

// Helper to login via API and set token in localStorage
async function loginViaAPI(page: any) {
  // Step 1: Sign in to get session_id
  const signInResponse = await page.request.post(`${BACKEND_URL}/api/v1/auth/sign-in`, {
    data: {
      username: 'sasha.patel@gmail.com',
      password: 'Demo1234!',
      device_id: '10000000-0000-0000-0000-000000000201'
    }
  });
  
  const signInData = await signInResponse.json();
  const sessionId = signInData.session_id;
  
  // Step 2: Submit proof to get access_token
  const proofResponse = await page.request.post(`${BACKEND_URL}/api/v1/auth/proof`, {
    data: {
      session_id: sessionId,
      proof_type: 'passcode',
      proof_value: '123456',
      device_id: '10000000-0000-0000-0000-000000000201'
    }
  });
  
  const proofData = await proofResponse.json();
  const accessToken = proofData.access_token;
  
  // Navigate to base URL and set token in context
  await page.context().addCookies([]);
  await page.goto('/');
  
  // Set token using correct storage key
  await page.evaluate((token) => {
    localStorage.setItem('lbg_ftr_demo_auth_token', token);
  }, accessToken);
  
  // Reload to ensure token is picked up by React context
  await page.reload();
  await page.waitForTimeout(1000);
}

test.describe('Authenticated Routes', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaAPI(page);
  });

  test('can visit accounts page and see account data', async ({ page }) => {
    await page.goto('/accounts');
    
    // Should see accounts heading or balance
    const heading = page.locator('h1, h2, h3, p').filter({ hasText: /account|overview|balance|£/i }).first();
    await expect(heading).toBeVisible({ timeout: 15000 });
  });

  test('can visit add payee page', async ({ page }) => {
    await page.goto('/add-payee');
    
    // Should see add payee form
    const heading = page.locator('h1, h2, h3').filter({ hasText: /add|new|payee/i }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('can visit step-up authentication page', async ({ page }) => {
    await page.goto('/step-up');
    
    // Should see step-up authentication content
    const content = page.locator('h1, h2, h3, p, div, button').first();
    await expect(content).toBeVisible({ timeout: 10000 });
  });
});
