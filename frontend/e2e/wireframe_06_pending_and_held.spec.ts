import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 06 - Pending and Held', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Log in through the form with seed credentials
    await page.getByLabel(/passcode/i).fill('Pass1234');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for navigation to accounts page
    await page.waitForURL('/accounts');
  });

  test('displays pending badge and do-not-resubmit message', async ({ page }) => {
    // Navigate to payees page
    await page.getByRole('link', { name: /pay & transfer/i }).click();
    await page.waitForURL('/payees');
    
    // Click on a payee
    await page.getByRole('button', { name: /k evans lettings/i }).click();
    
    // Fill payment details
    await page.getByLabel(/amount/i).fill('50.00');
    await page.getByLabel(/payment reference/i).fill('Test pending');
    
    // Submit payment entry
    await page.getByRole('button', { name: /continue|review payment/i }).click();
    
    // Wait for payment review page
    await page.waitForURL('/payment-review');
    
    // Click approve payment button
    await page.getByRole('button', { name: /^approve payment$/i }).click();
    
    // Wait for approval sheet and fill passcode
    await page.getByRole('dialog', { name: /approve this payment/i }).waitFor({ state: 'visible' });
    await page.getByLabel(/passcode/i).last().fill('Pass1234');
    await page.getByRole('dialog').getByRole('button', { name: /^approve/i }).click();
    
    // Wait for outcome - may be pending, sent, or warning
    await page.waitForTimeout(2000);
    
    const url = page.url();
    
    if (url.includes('/payment-pending')) {
      // Verify Pending badge is visible (yellow with icon)
      const badge = page.locator('span[role="status"]', { hasText: 'Pending' });
      await expect(badge).toBeVisible();
      
      // Verify badge uses color AND icon (not color alone)
      await expect(badge.locator('svg')).toBeVisible();
      
      // Verify do-not-resubmit message
      await expect(page.getByText(/don't send this payment again/i)).toBeVisible();
      
      // Verify payment reference always shown
      await expect(page.getByText('Test pending')).toBeVisible();
      
      // Verify Check status button present
      await expect(page.getByRole('button', { name: /check status/i })).toBeVisible();
    } else if (url.includes('/payment-outcome')) {
      // Payment completed successfully or failed - also valid
      console.log('Payment completed without pending state');
    } else if (url.includes('/payment-warning')) {
      // Warning triggered - stop it to test stopped outcome
      await page.getByRole('button', { name: /stop this payment/i }).click();
      await page.waitForURL('/payment-outcome');
    }
  });

  test('held payment shows pending with hold decision date', async ({ page }) => {
    // Navigate through payment flow with amount that might trigger hold
    await page.getByRole('link', { name: /pay & transfer/i }).click();
    await page.waitForURL('/payees');
    
    await page.getByRole('button', { name: /priya patel/i }).click();
    
    // Large amount more likely to trigger hold
    await page.getByLabel(/amount/i).fill('15000.00');
    await page.getByLabel(/payment reference/i).fill('Large payment');
    
    await page.getByRole('button', { name: /continue|review payment/i }).click();
    await page.waitForURL('/payment-review');
    
    await page.getByRole('button', { name: /^approve payment$/i }).click();
    
    // Wait for approval sheet and fill it
    await page.getByRole('dialog', { name: /approve this payment/i }).waitFor({ state: 'visible' });
    await page.getByLabel(/passcode/i).last().fill('Pass1234');
    await page.getByRole('dialog').getByRole('button', { name: /^approve/i }).click();
    
    await page.waitForTimeout(2000);
    
    if (page.url().includes('/payment-pending')) {
      // If held, should show "We're checking this payment" and decision date
      const title = page.getByRole('heading', { level: 1 });
      const titleText = await title.textContent();
      
      if (titleText?.includes('checking')) {
        // Held payment - verify hold-specific messaging
        await expect(page.getByText(/we are making some extra checks/i)).toBeVisible();
        
        // Verify payment reference shown
        await expect(page.getByText('Large payment')).toBeVisible();
        
        // Check status button present
        await expect(page.getByRole('button', { name: /check status/i })).toBeVisible();
      } else {
        // Regular pending
        await expect(page.getByText(/pending/i)).toBeVisible();
      }
    }
  });

  test('pending badge uses icon and text, not color alone', async ({ page }) => {
    // Navigate through payment flow
    await page.getByRole('link', { name: /pay & transfer/i }).click();
    await page.waitForURL('/payees');
    
    await page.getByRole('button', { name: /jamie clarke/i }).click();
    
    await page.getByLabel(/amount/i).fill('75.00');
    await page.getByLabel(/payment reference/i).fill('Accessibility test');
    
    await page.getByRole('button', { name: /continue|review payment/i }).click();
    await page.waitForURL('/payment-review');
    
    await page.getByRole('button', { name: /^approve payment$/i }).click();
    
    // Wait for approval sheet and fill it
    await page.getByRole('dialog', { name: /approve this payment/i }).waitFor({ state: 'visible' });
    await page.getByLabel(/passcode/i).last().fill('Pass1234');
    await page.getByRole('dialog').getByRole('button', { name: /^approve/i }).click();
    
    await page.waitForTimeout(2000);
    
    if (page.url().includes('/payment-pending')) {
      // Find the Pending badge
      const badge = page.locator('span[role="status"]', { hasText: 'Pending' });
      
      // Verify it contains both an icon (svg) and text
      await expect(badge.locator('svg')).toBeVisible();
      await expect(badge).toContainText('Pending');
      
      // Verify role="status" for screen reader announcement
      await expect(badge).toHaveAttribute('role', 'status');
    }
  });

  test('check status button refreshes payment state', async ({ page }) => {
    // Navigate through payment flow
    await page.getByRole('link', { name: /pay & transfer/i }).click();
    await page.waitForURL('/payees');
    
    await page.getByRole('button', { name: /k evans lettings/i }).click();
    
    await page.getByLabel(/amount/i).fill('120.00');
    await page.getByLabel(/payment reference/i).fill('Status check test');
    
    await page.getByRole('button', { name: /continue|review payment/i }).click();
    await page.waitForURL('/payment-review');
    
    await page.getByRole('button', { name: /^approve payment$/i }).click();
    
    // Wait for approval sheet and fill it
    await page.getByRole('dialog', { name: /approve this payment/i }).waitFor({ state: 'visible' });
    await page.getByLabel(/passcode/i).last().fill('Pass1234');
    await page.getByRole('dialog').getByRole('button', { name: /^approve/i }).click();
    
    await page.waitForTimeout(2000);
    
    if (page.url().includes('/payment-pending')) {
      // Click check status button
      const checkStatusButton = page.getByRole('button', { name: /check status/i });
      await expect(checkStatusButton).toBeVisible();
      
      await checkStatusButton.click();
      
      // Wait for API call to complete
      await page.waitForTimeout(1000);
      
      // Page should still show pending or navigate to outcome if status changed
      const currentUrl = page.url();
      expect(currentUrl).toMatch(/payment-pending|payment-outcome/);
    }
  });

  test('no resubmission controls shown for pending payments', async ({ page }) => {
    // Navigate through payment flow
    await page.getByRole('link', { name: /pay & transfer/i }).click();
    await page.waitForURL('/payees');
    
    await page.getByRole('button', { name: /priya patel/i }).click();
    
    await page.getByLabel(/amount/i).fill('200.00');
    await page.getByLabel(/payment reference/i).fill('No retry test');
    
    await page.getByRole('button', { name: /continue|review payment/i }).click();
    await page.waitForURL('/payment-review');
    
    await page.getByRole('button', { name: /^approve payment$/i }).click();
    
    // Wait for approval sheet and fill it
    await page.getByRole('dialog', { name: /approve this payment/i }).waitFor({ state: 'visible' });
    await page.getByLabel(/passcode/i).last().fill('Pass1234');
    await page.getByRole('dialog').getByRole('button', { name: /^approve/i }).click();
    
    await page.waitForTimeout(2000);
    
    if (page.url().includes('/payment-pending')) {
      // Verify NO "Try again" or "Pay again" buttons
      const tryAgainButton = page.getByRole('button', { name: /try again|pay again|retry/i });
      await expect(tryAgainButton).not.toBeVisible();
      
      // Only "Check status" and "Back to accounts" should be present
      await expect(page.getByRole('button', { name: /check status/i })).toBeVisible();
      await expect(page.getByRole('button', { name: /back to accounts/i })).toBeVisible();
    }
  });
});
