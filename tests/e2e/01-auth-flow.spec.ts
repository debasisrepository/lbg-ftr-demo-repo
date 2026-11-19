import { test, expect } from './_pipeline_guard';

test.describe('Authentication Flow', () => {
  test('can sign in through the form with valid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/');
    await expect(page).toHaveURL('/login');
    
    // Fill in the form using IDs
    await page.fill('#username', 'sasha.patel@gmail.com');
    await page.fill('#password', 'Demo1234!');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Should navigate to proof page
    await expect(page).toHaveURL('/proof', { timeout: 10000 });
    
    // Enter passcode using numeric keypad buttons
    const digits = ['1', '2', '3', '4', '5', '6'];
    for (const digit of digits) {
      await page.click(`button:has-text("${digit}")`);
      await page.waitForTimeout(100); // Small delay between keypad presses
    }
    
    // Should auto-submit and navigate to accounts page after 6 digits
    await expect(page).toHaveURL('/accounts', { timeout: 10000 });
    
    // Verify we're on the accounts page by checking for account information
    await expect(page.locator('h1, h2').filter({ hasText: /accounts|overview/i }).first()).toBeVisible({ timeout: 5000 });
  });

  test('shows validation error when username field is empty', async ({ page }) => {
    await page.goto('/login');
    
    // Fill only password
    await page.fill('#password', 'Demo1234!');
    
    // Try to submit
    await page.click('button[type="submit"]');
    
    // Should still be on login page
    await expect(page).toHaveURL('/login');
    
    // Should show validation error for username
    const errorMessage = page.locator('#username-error');
    await expect(errorMessage).toBeVisible({ timeout: 3000 });
  });

  test('shows validation error when password field is empty', async ({ page }) => {
    await page.goto('/login');
    
    // Fill only username
    await page.fill('#username', 'sasha.patel@gmail.com');
    
    // Try to submit
    await page.click('button[type="submit"]');
    
    // Should still be on login page
    await expect(page).toHaveURL('/login');
    
    // Should show validation error for password
    const errorMessage = page.locator('#password-error');
    await expect(errorMessage).toBeVisible({ timeout: 3000 });
  });

  test('shows generic error for invalid credentials', async ({ page, apiGuard }) => {
    // Allow 401 for this test - we expect authentication to fail
    apiGuard.allow(401, '/api/v1/auth/sign-in');
    
    await page.goto('/login');
    
    await page.fill('#username', 'wrong@example.com');
    await page.fill('#password', 'WrongPassword123!');
    
    await page.click('button[type="submit"]');
    
    // Should show generic error message (matches wireframe D text)
    const errorMessage = page.locator('text=/couldn\'t log you in|check them and try again/i');
    await expect(errorMessage).toBeVisible({ timeout: 5000 });
  });
});
