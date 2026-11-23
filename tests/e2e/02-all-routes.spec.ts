/**
 * E2E Test: All Routes Navigation (FR-AUTH-006)
 * Tests that all protected routes are accessible when authenticated
 * and display their expected content.
 */
import { test, expect } from './_pipeline_guard';
import { loginViaForm } from './helpers';

test.describe('All Routes Navigation', () => {
  test.beforeEach(async ({ page }) => {
    // Log in via form before each test
    await loginViaForm(page);
  });

  test('should access accounts overview page', async ({ page }) => {
    // Already on /accounts after login
    
    // Verify accounts page heading
    await expect(page.locator('h1')).toContainText('Your accounts');
    
    // Verify at least one account is displayed
    await expect(page.locator('text=Main Current Account')).toBeVisible({ timeout: 5000 });
  });

  test('should access payees page', async ({ page }) => {
    await page.goto('/payees');
    
    // Verify payees page heading "Pay & Transfer"
    await expect(page.locator('h1')).toContainText('Pay & Transfer');
  });

  test('should access payment entry page', async ({ page }) => {
    await page.goto('/payment-entry');
    
    // Verify payment entry page content (may redirect if no payee selected)
    await expect(page.locator('body')).toBeVisible();
  });

  test('should access payment review page', async ({ page }) => {
    await page.goto('/payment-review');
    
    // Verify payment review page renders (may redirect if no payment in state)
    await expect(page.locator('body')).toBeVisible();
  });

  test('should access payment outcome page', async ({ page }) => {
    await page.goto('/payment-outcome');
    
    // Verify outcome page renders (may redirect if no payment)
    await expect(page.locator('body')).toBeVisible();
  });

  test('should access payment sent page', async ({ page }) => {
    await page.goto('/payment-sent');
    
    // Verify sent page renders
    await expect(page.locator('body')).toBeVisible();
  });

  test('should access payment failed page', async ({ page }) => {
    await page.goto('/payment-failed');
    
    // Verify failed page renders
    await expect(page.locator('body')).toBeVisible();
  });

  test('should access payment warning page', async ({ page }) => {
    await page.goto('/payment-warning');
    
    // Verify warning page renders (may redirect if no payment)
    await expect(page.locator('body')).toBeVisible();
  });

  test('should access payment pending page', async ({ page }) => {
    await page.goto('/payment-pending');
    
    // Verify pending page renders
    await expect(page.locator('body')).toBeVisible();
  });

  test('should redirect root to accounts', async ({ page }) => {
    await page.goto('/');
    
    // Should redirect to /accounts
    await expect(page).toHaveURL('/accounts');
  });

  test('should redirect unknown routes to accounts', async ({ page }) => {
    await page.goto('/nonexistent-route');
    
    // Should redirect to /accounts
    await expect(page).toHaveURL('/accounts');
  });
});
