/**
 * Smoke test: Frontend infrastructure verification
 * 
 * Note: This test verifies the frontend infrastructure is correctly set up.
 * Auth endpoints will be implemented in a later task, so we test basic
 * infrastructure: page loads, backend connectivity, form renders.
 */

import { test, expect } from '@playwright/test';

test.describe('Smoke Infrastructure Test', () => {
  test('should load frontend and render login page', async ({ page }) => {
    // Navigate to the application
    await page.goto('/');

    // Should redirect to login page
    await expect(page).toHaveURL(/\/login/);

    // Verify login form elements exist
    const usernameInput = page.locator('input[name="username"], input[type="email"]').first();
    const passwordInput = page.locator('input[name="password"], input[type="password"]').first();
    const submitButton = page.locator('button[type="submit"]').first();

    await expect(usernameInput).toBeVisible();
    await expect(passwordInput).toBeVisible();
    await expect(submitButton).toBeVisible();

    // Verify seed credentials are pre-filled (from LoginPage defaults)
    await expect(usernameInput).toHaveValue('admin@example.com');
    await expect(passwordInput).toHaveValue('admin123');
  });

  test('should verify backend connectivity via health endpoint', async ({ page }) => {
    // Make a request to the backend health endpoint through the Vite proxy
    const response = await page.request.get('/api/health');
    
    expect(response.ok()).toBeTruthy();
    expect(response.status()).toBe(200);

    const body = await response.json();
    expect(body).toHaveProperty('status');
    expect(body.status).toBe('healthy');
  });

  test('should verify auth context and routing guard work', async ({ page }) => {
    // Try to access protected route without auth
    await page.goto('/dashboard');

    // Should redirect to login (RequireAuth guard)
    await expect(page).toHaveURL(/\/login/);

    // Verify no token in localStorage
    const token = await page.evaluate(() => {
      return localStorage.getItem('lbg_ftr_auth_token');
    });
    expect(token).toBeNull();
  });
});
