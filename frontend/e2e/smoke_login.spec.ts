import { test, expect } from './_pipeline_guard';

test('smoke login: user can log in with seed credentials and see dashboard', async ({ page }) => {
  // Navigate to login page
  await page.goto('/login');

  // Verify we're on the login page
  await expect(page.getByRole('heading', { name: /sign in to clear path/i })).toBeVisible();

  // Fill in the login form with seed credentials
  await page.getByLabel(/email/i).fill('admin@example.com');
  await page.getByLabel(/password/i).fill('admin123');

  // Submit the form
  await page.getByRole('button', { name: /sign in/i }).click();

  // Wait for navigation to complete and verify we're on the dashboard
  await expect(page).toHaveURL('/');
  
  // Verify dashboard content is visible
  await expect(page.getByRole('heading', { name: /dashboard/i })).toBeVisible();
  
  // Verify user email is shown in header
  await expect(page.getByText('admin@example.com')).toBeVisible();
  
  // Verify sign out button is present
  await expect(page.getByRole('button', { name: /sign out/i })).toBeVisible();
});

test('smoke login: invalid credentials show error', async ({ page }) => {
  await page.goto('/login');

  // Try to login with invalid credentials
  await page.getByLabel(/email/i).fill('wrong@example.com');
  await page.getByLabel(/password/i).fill('wrongpassword');
  await page.getByRole('button', { name: /sign in/i }).click();

  // Verify error message box is displayed (look for the error div, not specific text)
  await expect(page.locator('.bg-warn-bg')).toBeVisible();
  
  // Verify we're still on the login page
  await expect(page).toHaveURL('/login');
});

test('smoke login: protected route redirects to login when not authenticated', async ({ page }) => {
  // Try to access dashboard directly without logging in
  await page.goto('/');

  // Should be redirected to login
  await expect(page).toHaveURL('/login');
  await expect(page.getByRole('heading', { name: /sign in to clear path/i })).toBeVisible();
});
