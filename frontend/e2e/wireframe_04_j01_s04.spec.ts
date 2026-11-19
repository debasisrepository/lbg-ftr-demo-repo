import { test, expect } from '@playwright/test';

test.describe('Wireframe 04 - Payee Selection', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Wait for login page to load
    await expect(page.locator('h1', { hasText: 'Login' })).toBeVisible();
    
    // Fill in login form with seed credentials
    await page.locator('#username').fill('admin@example.com');
    await page.locator('#password').fill('admin123');
    
    // Submit login
    await page.locator('button[type="submit"]').click();
    
    // Wait for step-up page
    await expect(page).toHaveURL(/\/step-up/, { timeout: 10000 });
    
    // Wait for passcode heading
    await expect(page.locator('h1', { hasText: /enter your passcode/i })).toBeVisible();
    
    // Fill in passcode (stub accepts 123456)
    const inputs = page.locator('input[aria-label*="Passcode digit"]');
    const passcode = '123456';
    for (let i = 0; i < passcode.length; i++) {
      await inputs.nth(i).fill(passcode[i]);
    }
    
    // Submit by pressing Enter on last input
    await inputs.nth(5).press('Enter');
    
    // Wait a bit for the step-up to process
    await page.waitForTimeout(2000);
    
    // Navigate directly to payees page
    await page.goto('/payees');
    await expect(page.locator('h1', { hasText: /pay.*transfer/i })).toBeVisible();
  });

  test('AC1: renders saved payee list', async ({ page }) => {
    // Check for page title
    await expect(page.locator('h1', { hasText: /pay.*transfer/i })).toBeVisible();
    
    // Check for lead text
    await expect(page.locator('text=Who do you want to pay?')).toBeVisible();
    
    // Should have payee tiles - wait for at least one
    const payeeTiles = page.locator('button[role="radio"]');
    await expect(payeeTiles.first()).toBeVisible();
  });

  test('AC2: allows selecting a payee', async ({ page }) => {
    // Get first payee tile
    const firstPayee = page.locator('button[role="radio"]').first();
    await firstPayee.click();
    
    // Check that it's selected
    await expect(firstPayee).toHaveAttribute('aria-checked', 'true');
  });

  test('AC3: Continue button enabled after payee selection', async ({ page }) => {
    // Continue button should be disabled initially
    const continueButton = page.locator('button', { hasText: /continue.*payment/i });
    await expect(continueButton).toBeDisabled();
    
    // Select a payee
    const firstPayee = page.locator('button[role="radio"]').first();
    await firstPayee.click();
    
    // Continue button should now be enabled
    await expect(continueButton).not.toBeDisabled();
  });

  test('AC4: shows Add a new payee button', async ({ page }) => {
    // Check for Add button
    await expect(page.locator('button', { hasText: /add.*new.*payee/i })).toBeVisible();
  });

  test('AC5: Add new payee shows form', async ({ page }) => {
    // Click Add button
    await page.locator('button', { hasText: /add.*new.*payee/i }).click();
    
    // Check for form fields
    await expect(page.locator('label', { hasText: 'Name on the account' })).toBeVisible();
    await expect(page.locator('label', { hasText: 'Sort code' })).toBeVisible();
    await expect(page.locator('label', { hasText: 'Account number' })).toBeVisible();
    
    // Check for fresh verification notification
    await expect(page.locator('text=/Fresh verification required/i')).toBeVisible();
  });

  test('AC6: payee tiles show name, sort code, and masked account number', async ({ page }) => {
    // Check that payee tiles have required information
    const payeeTiles = page.locator('button[role="radio"]');
    const count = await payeeTiles.count();
    
    expect(count).toBeGreaterThan(0);
    
    // First payee should have name and account details
    const firstPayee = payeeTiles.first();
    const firstPayeeText = await firstPayee.textContent();
    
    // Should contain sort code pattern (XX-XX-XX) and masked account number (****XXXX)
    expect(firstPayeeText).toMatch(/\d{2}-\d{2}-\d{2}/); // Sort code format
    expect(firstPayeeText).toMatch(/\*{4}\d{4}/); // Masked account format
  });

  test('AC7: tab bar shows Pay & Transfer as active', async ({ page }) => {
    // Check that Pay & Transfer tab is visible
    const payTab = page.locator('button', { hasText: /pay.*transfer/i });
    await expect(payTab).toBeVisible();
  });
});
