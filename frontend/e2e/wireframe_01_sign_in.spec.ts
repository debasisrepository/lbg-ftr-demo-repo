import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 01 - Sign In', () => {
  test('should render sign-in page with form fields', async ({ page }) => {
    await page.goto('/login');

    // Check heading
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();

    // Check form elements
    await expect(page.getByLabel(/passcode/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();

    // Check hint text
    await expect(page.getByText(/4 to 12 characters/i)).toBeVisible();

    // Check protected content notice
    await expect(page.getByText(/protected content appears only after you sign in/i)).toBeVisible();
  });

  test('should login with seed credentials and redirect to accounts', async ({ page }) => {
    await page.goto('/login');

    // Fill in passcode with seed credentials
    await page.getByLabel(/passcode/i).fill('Pass1234');

    // Submit form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for redirect to accounts page
    await expect(page).toHaveURL(/\/accounts/, { timeout: 10000 });

    // Verify accounts page loaded
    await expect(page.getByRole('heading', { name: /your accounts/i })).toBeVisible({ timeout: 10000 });
  });

  test('should show error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill in wrong passcode
    await page.getByLabel(/passcode/i).fill('WrongPass1234');

    // Submit form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Wait for error message
    await expect(page.getByRole('alert')).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/sign-in failed/i)).toBeVisible();
    await expect(page.getByText(/we couldn't sign you in/i)).toBeVisible();
  });

  test('should validate passcode length', async ({ page }) => {
    await page.goto('/login');

    // Fill in too short passcode
    await page.getByLabel(/passcode/i).fill('ab');

    // Submit form
    await page.getByRole('button', { name: /sign in/i }).click();

    // Should show validation error (UI shows "Enter your passcode again")
    await expect(page.getByText(/enter your passcode again/i)).toBeVisible();
  });

  test('should clear error when user starts typing', async ({ page }) => {
    await page.goto('/login');

    // Trigger an error first
    await page.getByLabel(/passcode/i).fill('ab');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page.getByText(/enter your passcode again/i)).toBeVisible();

    // Start typing again
    await page.getByLabel(/passcode/i).fill('Pass');

    // Error should be cleared
    await expect(page.getByText(/enter your passcode again/i)).not.toBeVisible();
  });

  test('should have passcode input with correct attributes', async ({ page }) => {
    await page.goto('/login');

    const passcodeInput = page.getByLabel(/passcode/i);

    // Check input type
    await expect(passcodeInput).toHaveAttribute('type', 'password');

    // Check autocomplete
    await expect(passcodeInput).toHaveAttribute('autocomplete', 'current-password');

    // Check min/max length
    await expect(passcodeInput).toHaveAttribute('minlength', '4');
    await expect(passcodeInput).toHaveAttribute('maxlength', '12');
  });
});
