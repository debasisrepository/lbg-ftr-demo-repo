import { test, expect } from './_pipeline_guard';

/**
 * Smoke test: login via form with seed credentials and assert redirect to /cases
 */
test('login with seed credentials redirects to /cases', async ({ page }) => {
  // Navigate to login page
  await page.goto('/login');
  
  // Form should be visible with pre-filled values
  await expect(page.getByLabel(/email or username/i)).toHaveValue('admin@example.com');
  await expect(page.getByLabel(/password/i)).toHaveValue('admin123');
  
  // Submit the form
  await page.getByRole('button', { name: /sign in/i }).click();
  
  // Should redirect to /cases and show authenticated content
  await expect(page).toHaveURL('/cases');
  await expect(page.getByRole('heading', { name: /my cases/i })).toBeVisible();
});

test('invalid credentials stay on login page', async ({ page }) => {
  await page.goto('/login');
  
  // Change to invalid credentials
  await page.getByLabel(/email or username/i).fill('invalid@example.com');
  await page.getByLabel(/password/i).fill('wrongpassword');
  
  // Submit
  await page.getByRole('button', { name: /sign in/i }).click();
  
  // Should stay on login page (401 triggers redirect to /login in api-client)
  await expect(page).toHaveURL('/login');
  
  // Form should still be visible and functional
  await expect(page.getByLabel(/email or username/i)).toBeVisible();
  await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
});
