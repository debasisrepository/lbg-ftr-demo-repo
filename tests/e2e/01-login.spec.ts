/**
 * E2E Test: Login Flow (FR-AUTH-003)
 * Tests the passcode sign-in through the actual form submission.
 */
import { test, expect } from './_pipeline_guard';

test.describe('Login Flow', () => {
  test('should log in through the form with valid credentials and redirect to accounts', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Verify the login page loaded
    await expect(page.locator('h1')).toContainText('Sign in');
    
    // Fill in the passcode field
    await page.fill('input[type="password"]', 'Pass1234');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Wait for navigation after login
    await page.waitForURL('/accounts', { timeout: 10000 });
    
    // Verify we're on the accounts page
    await expect(page).toHaveURL('/accounts');
    
    // Verify accounts page content is visible
    await expect(page.locator('h1')).toContainText('Your accounts');
  });

  test('should reject invalid passcode', async ({ page, apiGuard }) => {
    // Allow 401 error for invalid credentials
    apiGuard.allow(401, '/auth/login');
    
    await page.goto('/login');
    
    // Fill in invalid passcode
    await page.fill('input[type="password"]', 'WrongPass');
    
    // Submit the form
    await page.click('button[type="submit"]');
    
    // Verify error message appears (look for any error text)
    await expect(page.locator('text=/Sign-in failed|Invalid|incorrect/i')).toBeVisible({ timeout: 5000 });
    
    // Verify we're still on login page
    await expect(page).toHaveURL('/login');
  });

  test('should validate passcode length client-side', async ({ page }) => {
    await page.goto('/login');
    
    // Try to submit with short passcode
    await page.fill('input[type="password"]', 'ab');
    await page.click('button[type="submit"]');
    
    // Verify validation error appears
    const errorAlert = page.locator('[role="alert"]');
    await expect(errorAlert).toBeVisible({ timeout: 3000 });
    await expect(errorAlert).toContainText(/between 4 and 12|too short|invalid/i);
  });
});
