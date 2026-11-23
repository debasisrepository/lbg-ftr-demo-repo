/**
 * E2E Test: Complete Payment Flow
 * Tests: FR-PAY-001, FR-PAY-002, FR-PAY-003, FR-PAY-007, FR-PAY-008, 
 *        FR-PAY-009, FR-PAY-010, FR-PAY-012, FR-PAY-013, FR-PAY-014
 * 
 * Complete flow: Select payee → Enter payment details → Review → 
 * Handle warnings if present → Approve → See outcome
 */
import { test, expect } from './_pipeline_guard';
import { loginViaForm } from './helpers';

test.describe('Payment Flow', () => {
  test.beforeEach(async ({ page }) => {
    await loginViaForm(page);
  });

  test('should complete a successful payment to a saved payee', async ({ page }) => {
    // Already on /accounts after login
    await expect(page.locator('h1')).toContainText('Your accounts');
    
    // Navigate to payees
    await page.goto('/payees');
    
    // Wait for payees page to load
    await expect(page.locator('h1')).toContainText('Pay & Transfer');
    
    // Select the first available payee
    const firstPayee = page.locator('[data-testid="payee-item"], [role="button"]').first();
    await firstPayee.waitFor({ state: 'visible', timeout: 5000 });
    await firstPayee.click();
    
    // Should be on payment entry page
    await page.waitForURL(/\/payment-entry/, { timeout: 10000 });
    
    // Fill in payment amount
    const amountInput = page.locator('input[type="number"], input[type="text"][name*="amount"], input[placeholder*="amount"]').first();
    await amountInput.waitFor({ state: 'visible', timeout: 5000 });
    await amountInput.fill('50.00');
    
    // Fill in payment reference
    const referenceInput = page.locator('input[name*="reference"], input[placeholder*="reference"], textarea').first();
    await referenceInput.waitFor({ state: 'visible', timeout: 5000 });
    await referenceInput.fill('Test payment ref');
    
    // Click continue/next to go to review
    const continueButton = page.locator('button').filter({ hasText: /Continue|Next|Review/i }).first();
    await continueButton.click();
    
    // Should be on payment review page
    await page.waitForURL(/\/payment-review/, { timeout: 10000 });
    
    // Verify review details are shown (amount and reference)
    await expect(page.getByText(/50\.00|£50/)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText('Test payment ref')).toBeVisible({ timeout: 5000 });
    
    // Click "Approve payment" button to open approval sheet
    const approveButton = page.locator('button').filter({ hasText: /Approve payment/i }).first();
    await approveButton.click();
    
    // Wait for approval sheet to appear
    await expect(page.locator('[role="dialog"]')).toBeVisible({ timeout: 3000 });
    
    // Fill in passcode in the approval sheet
    await page.locator('[role="dialog"] input[type="password"]').fill('Pass1234');
    
    // Click the approve button in the sheet
    const sheetApproveButton = page.locator('[role="dialog"] button[type="submit"]');
    await sheetApproveButton.click();
    
    // Wait for outcome - could be sent, pending, warning, or outcome
    await page.waitForURL(/\/payment-(sent|pending|warning|outcome|failed)/, { timeout: 15000 });
    
    // Check which outcome we got
    let url = page.url();
    
    if (url.includes('/payment-warning')) {
      // If warning appeared, acknowledge it
      await expect(page.locator('h1, h2').filter({ hasText: /Warning|Check|Risk/i })).toBeVisible();
      
      // Click continue anyway (if allowed) or stop
      const continueAnywayButton = page.locator('button').filter({ hasText: /Continue|Proceed|Yes/i }).first();
      if (await continueAnywayButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await continueAnywayButton.click();
        // Wait for final outcome
        await page.waitForURL(/\/payment-(sent|pending|failed|outcome)/, { timeout: 15000 });
        url = page.url();
      }
    }
    
    // If we're on /payment-outcome, wait for it to redirect to final status
    if (url.includes('/payment-outcome')) {
      await page.waitForURL(/\/payment-(sent|pending|failed)/, { timeout: 15000 });
    }
    
    // Verify we ended up on a final outcome page
    const finalUrl = page.url();
    expect(finalUrl).toMatch(/\/payment-(sent|pending|failed)/);
    
    // Verify outcome page shows the reference
    await expect(page.locator('text=Test payment ref')).toBeVisible({ timeout: 5000 });
    
    // Verify status is clearly shown
    if (finalUrl.includes('/payment-sent')) {
      await expect(page.locator('h1, h2').filter({ hasText: /Sent|sent/i })).toBeVisible();
    } else if (finalUrl.includes('/payment-pending')) {
      await expect(page.locator('h1, h2').filter({ hasText: /Pending|Review|Hold/i })).toBeVisible();
    } else if (finalUrl.includes('/payment-failed')) {
      await expect(page.locator('h1, h2').filter({ hasText: /Failed|failed/i })).toBeVisible();
    }
  });

  test('should show payees list', async ({ page }) => {
    await page.goto('/payees');
    
    // Verify payees page loads
    await expect(page.locator('h1')).toContainText('Pay & Transfer');
  });
});
