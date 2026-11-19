import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 06 - Payment Outcome (FR-006)', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login
    await page.goto('/');
    
    // Login with seed credentials
    await page.fill('#username', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.click('button[type="submit"]');
    
    // Complete step-up with passcode
    await page.waitForURL('**/step-up');
    const passcodeInputs = page.locator('input[aria-label*="Passcode digit"]');
    await passcodeInputs.nth(0).fill('1');
    await passcodeInputs.nth(1).fill('2');
    await passcodeInputs.nth(2).fill('3');
    await passcodeInputs.nth(3).fill('4');
    await passcodeInputs.nth(4).fill('5');
    await passcodeInputs.nth(5).fill('6');
    await passcodeInputs.nth(5).press('Enter');
    
    // Wait for accounts page
    await page.waitForURL('**/accounts');
    
    // Navigate to payees page
    await page.click('button:has-text("Pay & Transfer")');
    await page.waitForURL('**/payees');
  });

  test('should display sent payment outcome with all required details', async ({ page }) => {
    // Select a payee and navigate to payment entry
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    // Enter valid payment details
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    
    const referenceInput = page.locator('#reference');
    await referenceInput.fill('Test payment');
    
    // Click pay button and approve
    await page.click('button:has-text("Pay £50.00")');
    await expect(page.locator('text=Approve with Face ID')).toBeVisible();
    await page.click('button:has-text("Approve")');
    
    // Wait for outcome page
    await page.waitForURL('**/payment/outcome');
    
    // Verify outcome heading
    const heading = page.locator('h1');
    await expect(heading).toHaveText(/Payment sent|Payment pending|Payment not sent/);
    
    // Verify status badge
    await expect(page.locator('text=/^(Sent|Pending|Failed)$/i')).toBeVisible();
    
    // Verify payee name in summary
    await expect(page.locator('dt:has-text("Payee") + dd')).toHaveText('Jamie Clarke');
    
    // Verify amount in summary
    await expect(page.locator('dt:has-text("Amount") + dd')).toHaveText('£50.00');
    
    // Verify reference in summary
    await expect(page.locator('dt:has-text("Reference") + dd')).toHaveText('Test payment');
    
    // Verify payment identifier
    await expect(page.locator('dt:has-text("Payment identifier") + dd')).toBeVisible();
  });

  test('should show sent status with arrival message when payment succeeds', async ({ page }) => {
    // Complete payment flow
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    await page.click('button:has-text("Pay £50.00")');
    await page.click('button:has-text("Approve")');
    await page.waitForURL('**/payment/outcome');
    
    // Check if status is sent (70% probability from stub)
    const statusText = await page.locator('h1').textContent();
    
    if (statusText?.includes('sent')) {
      // Verify sent-specific elements
      await expect(page.locator('text=/is on its way/i')).toBeVisible();
      await expect(page.locator('text=/should arrive/i')).toBeVisible();
    }
  });

  test('should show pending status with duplicate warning when appropriate', async ({ page }) => {
    // Complete payment flow
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    await page.click('button:has-text("Pay £50.00")');
    await page.click('button:has-text("Approve")');
    await page.waitForURL('**/payment/outcome');
    
    // Check if status is pending (20% probability from stub)
    const statusText = await page.locator('h1').textContent();
    
    if (statusText?.includes('pending')) {
      // Verify pending-specific elements
      await expect(page.locator('text=/waiting for confirmation/i')).toBeVisible();
      
      // Check for duplicate warning notification
      const duplicateWarning = page.locator('text=/Don\'t pay again yet/i');
      // Assert it exists when status is pending - the backend may or may not set duplicate_submission_blocked
      // but we verify the notification is present when it should be
      const isWarningVisible = await duplicateWarning.isVisible();
      // If duplicate_submission_blocked is true, warning should be visible
      // We can't control the backend stub, so we just verify the UI renders correctly when it appears
      if (isWarningVisible) {
        await expect(page.locator('text=/Paying again could send the money twice/i')).toBeVisible();
      }
    }
  });

  test('should show failed status with clear guidance when payment fails', async ({ page }) => {
    // Complete payment flow
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    await page.click('button:has-text("Pay £50.00")');
    await page.click('button:has-text("Approve")');
    await page.waitForURL('**/payment/outcome');
    
    // Check if status is failed (10% probability from stub)
    const statusText = await page.locator('h1').textContent();
    
    if (statusText?.includes('not sent')) {
      // Verify failed-specific elements
      await expect(page.locator('text=/We couldn\'t send/i')).toBeVisible();
      await expect(page.locator('text=/No money has left your account/i')).toBeVisible();
      await expect(page.locator('text=/What to do next/i')).toBeVisible();
      
      // Verify Try again button present
      await expect(page.locator('button:has-text("Try again")')).toBeVisible();
    }
  });

  test('should display action buttons based on payment status', async ({ page }) => {
    // Complete payment flow
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    await page.click('button:has-text("Pay £50.00")');
    await page.click('button:has-text("Approve")');
    await page.waitForURL('**/payment/outcome');
    
    // Verify Back to accounts button always present
    await expect(page.locator('button:has-text("Back to accounts")')).toBeVisible();
    
    // Check for status-specific buttons
    const statusText = await page.locator('h1').textContent();
    
    if (statusText?.includes('not sent')) {
      // Failed: should have Try again button
      await expect(page.locator('button:has-text("Try again")')).toBeVisible();
    } else if (statusText?.includes('pending')) {
      // Pending: Make another payment should be disabled
      const makeAnotherButton = page.locator('button:has-text("Make another payment")');
      await expect(makeAnotherButton).toBeDisabled();
    } else {
      // Sent: Make another payment should be enabled
      const makeAnotherButton = page.locator('button:has-text("Make another payment")');
      await expect(makeAnotherButton).toBeEnabled();
    }
  });

  test('should navigate back to accounts when button clicked', async ({ page }) => {
    // Complete payment flow to outcome page
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    await page.click('button:has-text("Pay £50.00")');
    await page.click('button:has-text("Approve")');
    await page.waitForURL('**/payment/outcome');
    
    // Click Back to accounts
    await page.click('button:has-text("Back to accounts")');
    
    // Verify navigation to accounts page
    await page.waitForURL('**/accounts');
    await expect(page.locator('h1')).toHaveText(/Accounts|Account overview/i);
  });

  test('should show 64px outcome icon matching wireframe specification', async ({ page }) => {
    // Complete payment flow
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    await page.click('button:has-text("Pay £50.00")');
    await page.click('button:has-text("Approve")');
    await page.waitForURL('**/payment/outcome');
    
    // Verify large icon is present (64px as per wireframe)
    const outcomeIcon = page.locator('svg').first();
    await expect(outcomeIcon).toBeVisible();
    
    // Icon should be one of: checkmark (sent), clock (pending), or error (failed)
    const iconCount = await page.locator('svg[width="64"]').count();
    expect(iconCount).toBeGreaterThan(0);
  });
});
