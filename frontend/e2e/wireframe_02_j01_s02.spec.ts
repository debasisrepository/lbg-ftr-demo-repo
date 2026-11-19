/**
 * E2E test for wireframe_02_j01_s02 - FR-002 Prove it's her
 * Tests step-up authentication with passcode and biometric
 */

import { test, expect } from '@playwright/test';

test.describe('Wireframe 02 - Step-up authentication (FR-002)', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login and sign in with seed credentials
    await page.goto('/login');
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
    
    // Fill in the login form with seed credentials
    await page.getByLabel(/username/i).fill('admin@example.com');
    await page.getByLabel(/password/i).fill('admin123');
    
    // Submit the form
    await page.getByRole('button', { name: /continue/i }).click();
    
    // Wait for navigation to step-up
    await expect(page).toHaveURL(/\/step-up/, { timeout: 10000 });
  });

  test('verifies step-up with correct passcode and advances to accounts (AC1)', async ({ page }) => {
    // Verify page heading
    await expect(page.getByRole('heading', { name: /enter your passcode/i })).toBeVisible();
    await expect(page.getByText('Enter the 6-digit passcode you created when you opened your account.')).toBeVisible();

    // Enter correct passcode (stub accepts "123456")
    const inputs = page.getByLabel(/passcode digit/i);
    const digits = ['1', '2', '3', '4', '5', '6'];
    
    for (let i = 0; i < 6; i++) {
      await inputs.nth(i).fill(digits[i]);
    }

    // Submit by pressing Enter on last input
    await inputs.nth(5).press('Enter');

    // Should navigate to accounts page
    await expect(page).toHaveURL(/\/accounts/, { timeout: 10000 });
    await expect(page.getByRole('heading', { name: /accounts/i })).toBeVisible();
  });

  test('shows remaining attempts after wrong passcode', async ({ page }) => {
    // Enter incorrect passcode
    const inputs = page.getByLabel(/passcode digit/i);
    const wrongDigits = ['9', '9', '9', '9', '9', '9'];
    
    for (let i = 0; i < 6; i++) {
      await inputs.nth(i).fill(wrongDigits[i]);
    }

    await inputs.nth(5).press('Enter');

    // Wait for error message to appear
    await page.waitForTimeout(1000);

    // Should show error with remaining attempts
    await expect(page.getByText(/your passcode is incorrect/i)).toBeVisible();
    await expect(page.getByText(/you have \d+ attempts? left/i)).toBeVisible();
  });

  test('shows passcode when toggle is clicked', async ({ page }) => {
    const inputs = page.getByLabel(/passcode digit/i);
    const showPasscodeButton = page.getByRole('button', { name: /show passcode/i });

    // Passcode should be masked initially
    await expect(inputs.nth(0)).toHaveAttribute('type', 'password');

    // Click show passcode
    await showPasscodeButton.click();
    await expect(inputs.nth(0)).toHaveAttribute('type', 'text');

    // Click again to hide
    await showPasscodeButton.click();
    await expect(inputs.nth(0)).toHaveAttribute('type', 'password');
  });

  test('auto-focuses next input when digit is entered', async ({ page }) => {
    const inputs = page.getByLabel(/passcode digit/i);

    // Fill first input
    await inputs.nth(0).fill('1');

    // Second input should be focused
    await expect(inputs.nth(1)).toBeFocused();

    // Fill second input
    await inputs.nth(1).fill('2');

    // Third input should be focused
    await expect(inputs.nth(2)).toBeFocused();
  });

  test('navigates back with backspace when input is empty', async ({ page }) => {
    const inputs = page.getByLabel(/passcode digit/i);

    // Focus second input
    await inputs.nth(1).focus();

    // Press backspace when empty
    await inputs.nth(1).press('Backspace');

    // First input should be focused
    await expect(inputs.nth(0)).toBeFocused();
  });

  test('shows helper text about 3-attempt lockout', async ({ page }) => {
    await expect(page.getByText(/after three wrong passcodes, passcode sign-in pauses/i)).toBeVisible();
  });
});
