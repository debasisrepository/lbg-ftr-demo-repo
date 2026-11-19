/**
 * E2E test for wireframe_01_j01_s01 - FR-001 Sign in
 * Tests login flow from wireframe action through to step-up navigation
 */

import { test, expect } from '@playwright/test';

test.describe('Wireframe 01 - Sign in (FR-001)', () => {
  test('logs in with seed credentials and advances to step-up', async ({ page }) => {
    // Navigate to login page
    await page.goto('/');
    
    // Should be redirected to login
    await expect(page).toHaveURL('/login');

    // Verify page heading and elements
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
    await expect(page.getByText('Use the username and password you set up when you opened your account.')).toBeVisible();

    // Verify seed credentials are pre-filled
    const usernameInput = page.getByLabel(/username/i);
    const passwordInput = page.getByLabel(/password/i);
    
    await expect(usernameInput).toHaveValue('admin@example.com');
    await expect(passwordInput).toHaveValue('admin123');

    // Submit the form
    const continueButton = page.getByRole('button', { name: /continue/i });
    await continueButton.click();

    // Wait for success notification
    await expect(page.getByText('Details accepted')).toBeVisible();

    // Should navigate to step-up page
    await expect(page).toHaveURL(/\/step-up/);
    
    // Verify step-up page loaded with correct content
    await expect(page.getByRole('heading', { name: /enter your passcode/i })).toBeVisible();
  });

  test('shows inline validation for empty fields (AC1)', async ({ page }) => {
    await page.goto('/login');

    // Clear the pre-filled values
    const usernameInput = page.getByLabel(/username/i);
    const passwordInput = page.getByLabel(/password/i);
    
    await usernameInput.clear();
    await passwordInput.clear();

    // Try to submit
    await page.getByRole('button', { name: /continue/i }).click();

    // Should show validation errors
    await expect(page.getByText('Enter your username.')).toBeVisible();
    await expect(page.getByText('Enter your password.')).toBeVisible();
  });

  test('shows generic error for incorrect credentials (AC2)', async ({ page }) => {
    await page.goto('/login');

    // Enter incorrect credentials
    const usernameInput = page.getByLabel(/username/i);
    const passwordInput = page.getByLabel(/password/i);
    
    await usernameInput.fill('wrong@example.com');
    await passwordInput.fill('wrongpassword');

    await page.getByRole('button', { name: /continue/i }).click();

    // Wait for error notification text to appear
    // Should show generic error message (does not reveal which credential was wrong)
    await expect(page.getByText("We couldn't sign you in with those details.")).toBeVisible();
  });

  test('shows password when toggle is clicked', async ({ page }) => {
    await page.goto('/login');

    const passwordInput = page.getByLabel(/password/i);
    const showPasswordButton = page.getByRole('button', { name: /show password/i });

    // Password should be masked initially
    await expect(passwordInput).toHaveAttribute('type', 'password');

    // Click show password
    await showPasswordButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'text');

    // Click again to hide
    await showPasswordButton.click();
    await expect(passwordInput).toHaveAttribute('type', 'password');
  });
});
