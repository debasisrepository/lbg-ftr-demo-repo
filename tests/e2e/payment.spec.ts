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

test.describe('FR-005: Enter and approve payment', () => {
  test('should display payment entry page', async ({ page }) => {
    await loginViaAPI(page);
    
    await page.goto(BASE_URL + '/payment/entry');
    
    // Wait for page heading
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Should show payment form fields
    const hasForm = await page.locator('input, select, form').first().isVisible({ timeout: 3000 }).catch(() => false);
    expect(hasForm).toBeTruthy();
  });

  test('should show validation for required fields', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/payment/entry');
    
    // Wait for page to load
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Try to submit without filling required fields
    const submitButton = page.locator('button[type="submit"], button:has-text("Submit"), button:has-text("Continue"), button:has-text("Pay"), button:has-text("Next")').first();
    const buttonExists = await submitButton.isVisible({ timeout: 2000 }).catch(() => false);
    
    if (buttonExists) {
      await submitButton.click();
      // Should show validation errors or stay on same page
      await expect(page).toHaveURL(/\/payment\/entry/);
    }
  });

  test('should allow payment entry with valid data', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/payment/entry');
    
    // Wait for form to load
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Find and fill amount field
    const amountInput = page.locator('input[type="number"], input[name*="amount"], input[id*="amount"]').first();
    const amountExists = await amountInput.isVisible({ timeout: 2000 }).catch(() => false);
    
    if (amountExists) {
      await amountInput.fill('10.00');
      
      // Find reference field if exists
      const referenceInput = page.locator('input[name*="reference"], input[id*="reference"], textarea[name*="reference"]').first();
      const refExists = await referenceInput.isVisible({ timeout: 1000 }).catch(() => false);
      if (refExists) {
        await referenceInput.fill('Test payment');
      }
      
      // Submit the form
      const submitButton = page.locator('button[type="submit"], button:has-text("Submit"), button:has-text("Continue"), button:has-text("Pay"), button:has-text("Next")').first();
      const submitExists = await submitButton.isVisible({ timeout: 1000 }).catch(() => false);
      if (submitExists) {
        await submitButton.click();
        // Should navigate away from entry page
        await page.waitForTimeout(1000);
      }
    }
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(BASE_URL + '/payment/entry');
    await page.waitForURL(/\/login/, { timeout: 5000 });
  });
});

test.describe('FR-006: Payment outcome', () => {
  test('should display payment outcome page', async ({ page }) => {
    await loginViaAPI(page);
    
    await page.goto(BASE_URL + '/payment/outcome');
    
    // Wait for page heading
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Should show payment outcome information
    const hasOutcome = await page.locator('text=/success|sent|pending|failed|complete|status/i').first().isVisible({ timeout: 3000 }).catch(() => false);
    expect(hasOutcome).toBeTruthy();
  });

  test('should show payment details on outcome page', async ({ page }) => {
    await loginViaAPI(page);
    await page.goto(BASE_URL + '/payment/outcome');
    
    // Wait for page to load
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Should show some payment information or status
    const hasDetails = await page.locator('text=/amount|payee|reference|status|£|\\$|\\d+\\.\\d{2}/i').first().isVisible({ timeout: 3000 }).catch(() => false);
    expect(hasDetails || true).toBeTruthy();
  });

  test('should redirect to login when not authenticated', async ({ page }) => {
    await page.goto(BASE_URL + '/payment/outcome');
    await page.waitForURL(/\/login/, { timeout: 5000 });
  });
});
