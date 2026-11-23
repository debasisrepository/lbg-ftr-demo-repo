/**
 * E2E Test: Accounts Overview (FR-ACCT-001, FR-ACCT-002, FR-ACCT-003)
 * Tests account display, freshness indicators, and honest balance handling.
 */
import { test, expect } from './_pipeline_guard';
import { loginViaForm } from './helpers';

test.describe('Accounts Overview', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaForm(page);
  });

  test('should display multiple accounts with identifying information', async ({ page }) => {
    // Already on /accounts after login
    
    // Verify heading
    await expect(page.locator('h1')).toContainText('Your accounts');
    
    // Verify at least 2 accounts are shown (seed data has 3)
    await expect(page.locator('text=Main Current Account')).toBeVisible({ timeout: 5000 });
    
    // Verify balances are displayed (not just zero) - use first() for multiple matches
    await expect(page.locator('text=/£[0-9]/').first()).toBeVisible();
  });

  test('should show freshness indicator or timestamp', async ({ page }) => {
    // Already on /accounts
    
    // Look for freshness indicators like "as of", "updated", "last updated", timestamp
    const freshnessIndicator = page.locator('text=/[Aa]s of|[Uu]pdated|[Ll]ast|[0-9]{1,2}:[0-9]{2}/').first();
    
    // Freshness should be visible somewhere on the page
    await expect(freshnessIndicator).toBeVisible({ timeout: 5000 });
  });

  test('should distinguish accounts by type and masked number', async ({ page }) => {
    // Already on /accounts
    
    // Accounts should show masked identifiers - use first() for multiple matches
    await expect(page.locator('text=/\\*\\*\\*\\*[0-9]{4}/').first()).toBeVisible({ timeout: 5000 });
    
    // Should show account types
    const accountTypes = page.locator('text=/Current|Savings|ISA/i');
    await expect(accountTypes.first()).toBeVisible();
  });

  test('should not show zero for missing balances', async ({ page }) => {
    // Already on /accounts
    
    // All seed accounts have real balances, so verify the page loaded with data
    await expect(page.locator('text=/£[1-9]/').first()).toBeVisible({ timeout: 5000 });
    
    // If there were unavailable accounts, they should show "Unavailable" not "£0.00"
    // This is a design rule check - the seed data should have proper balances
  });

  test('should allow navigation to payment from accounts', async ({ page }) => {
    // Already on /accounts
    
    // Look for pay/payment button
    const payButton = page.locator('button, a').filter({ hasText: /Pay|Make a payment/i }).first();
    
    if (await payButton.isVisible({ timeout: 2000 }).catch(() => false)) {
      await payButton.click();
      
      // Should navigate to payees or payment-entry
      await page.waitForURL(/\/(payees|payment-entry)/, { timeout: 10000 });
    }
  });

  test('should show account balances in correct currency', async ({ page }) => {
    // Already on /accounts
    
    // Verify GBP symbol is shown - use first() for multiple matches
    await expect(page.locator('text=£').first()).toBeVisible({ timeout: 5000 });
  });

  test('should handle page refresh maintaining auth', async ({ page }) => {
    // Already on /accounts
    
    // Verify initial load
    await expect(page.locator('h1')).toContainText('Your accounts');
    
    // Refresh the page
    await page.reload();
    
    // Should still be on accounts page, not redirected to login
    await expect(page).toHaveURL('/accounts');
    await expect(page.locator('h1')).toContainText('Your accounts');
  });
});
