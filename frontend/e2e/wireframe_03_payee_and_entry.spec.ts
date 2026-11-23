import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 03 - Payee Selection and Payment Entry', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto('/');
    
    // Log in with seed credentials through the form by typing and submitting
    const passcodeInput = page.getByLabel('Passcode');
    await passcodeInput.fill('Pass1234');
    
    const submitButton = page.getByRole('button', { name: 'Sign in' });
    await submitButton.click();
    
    // Wait for redirect to accounts page
    await page.waitForURL('/accounts');
  });

  test('should display saved payees list', async ({ page }) => {
    // Navigate to payees page
    await page.click('a:has-text("Pay & Transfer")');
    await page.waitForURL('/payees');

    // Check page title
    await expect(page.locator('h1')).toContainText('Pay & Transfer');

    // Check section heading
    await expect(page.getByText('Pay someone')).toBeVisible();

    // Check all three seed payees are displayed
    await expect(page.getByText('Jamie Clarke')).toBeVisible();
    await expect(page.getByText(/Sort code 04-00-04, account ending \*\*\*\*3321/)).toBeVisible();

    await expect(page.getByText('Priya Patel')).toBeVisible();
    await expect(page.getByText(/Sort code 60-83-71, account ending \*\*\*\*7745/)).toBeVisible();

    await expect(page.getByText('K Evans Lettings')).toBeVisible();
    await expect(page.getByText(/Sort code 20-45-77, account ending \*\*\*\*9842/)).toBeVisible();

    // Check hint text
    await expect(page.getByText(/Choose a payee to start a payment/)).toBeVisible();
    await expect(page.getByText(/Full account numbers are never shown/)).toBeVisible();
  });

  test('should navigate to payment entry when payee is selected', async ({ page }) => {
    // Navigate to payees page
    await page.click('a:has-text("Pay & Transfer")');
    await page.waitForURL('/payees');

    // Click on K Evans Lettings payee
    await page.click('button:has-text("K Evans Lettings")');

    // Wait for navigation to payment entry
    await page.waitForURL('/payment-entry');

    // Check payment entry page title includes payee name
    await expect(page.locator('h1')).toContainText('Pay K Evans Lettings');
    await expect(page.getByText(/Sort code 20-45-77, account ending \*\*\*\*9842/)).toBeVisible();
  });

  test('should display payment entry form with all fields', async ({ page }) => {
    // Navigate to payees and select one
    await page.click('a:has-text("Pay & Transfer")');
    await page.waitForURL('/payees');
    await page.click('button:has-text("K Evans Lettings")');
    await page.waitForURL('/payment-entry');

    // Check form fields exist
    await expect(page.getByLabel('From')).toBeVisible();
    await expect(page.getByLabel(/Amount/)).toBeVisible();
    await expect(page.getByLabel(/Payment reference/)).toBeVisible();

    // Check hint texts
    await expect(page.getByText(/Only accounts that can be paid from are listed/)).toBeVisible();
    await expect(page.getByText(/Enter pounds and pence, for example 250.00/)).toBeVisible();
    await expect(page.getByText(/1 to 18 characters. The payee sees this on their statement/)).toBeVisible();

    // Check submit button exists and is initially disabled
    const submitButton = page.getByRole('button', { name: /Review payment/i });
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toBeDisabled();
  });

  test('should show character counter for payment reference', async ({ page }) => {
    // Navigate to payment entry
    await page.click('a:has-text("Pay & Transfer")');
    await page.click('button:has-text("K Evans Lettings")');
    await page.waitForURL('/payment-entry');

    // Check initial counter
    await expect(page.getByText('0 of 18')).toBeVisible();

    // Type in reference field
    const referenceInput = page.getByLabel(/Payment reference/);
    await referenceInput.fill('Invoice 2041');

    // Check updated counter
    await expect(page.getByText('12 of 18')).toBeVisible();
  });

  test('should validate form and show errors when incomplete', async ({ page }) => {
    // Navigate to payment entry
    await page.click('a:has-text("Pay & Transfer")');
    await page.click('button:has-text("K Evans Lettings")');
    await page.waitForURL('/payment-entry');

    // Fill in invalid amount
    await page.fill('input[name="amount"]', '0.00');

    // Try to submit without reference
    const submitButton = page.getByRole('button', { name: /Review payment/i });
    
    // Button should still be disabled
    await expect(submitButton).toBeDisabled();

    // Add reference to enable button
    await page.fill('input[name="payment_reference"]', 'Invoice');
    
    // Amount is still 0, so button still disabled
    await expect(submitButton).toBeDisabled();
  });

  test('should enable submit button when form is complete and valid', async ({ page }) => {
    // Navigate to payment entry
    await page.click('a:has-text("Pay & Transfer")');
    await page.click('button:has-text("K Evans Lettings")');
    await page.waitForURL('/payment-entry');

    // Fill in all fields with valid data
    await page.fill('input[name="amount"]', '250.00');
    await page.fill('input[name="payment_reference"]', 'Invoice 2041');

    // Submit button should now be enabled
    const submitButton = page.getByRole('button', { name: /Review payment/i });
    await expect(submitButton).not.toBeDisabled();
  });

  test('should create payment and navigate to review page', async ({ page }) => {
    // Navigate to payment entry
    await page.click('a:has-text("Pay & Transfer")');
    await page.click('button:has-text("K Evans Lettings")');
    await page.waitForURL('/payment-entry');

    // Fill in form
    await page.fill('input[name="amount"]', '250.00');
    await page.fill('input[name="payment_reference"]', 'Invoice 2041');

    // Submit form
    await page.click('button[type="submit"]:has-text("Review payment")');

    // Wait for navigation to review page
    await page.waitForURL('/payment-review');

    // Check review page shows correct details
    await expect(page.locator('h1')).toContainText('Review your payment');
    await expect(page.getByText('K Evans Lettings')).toBeVisible();
    await expect(page.getByText('£250.00')).toBeVisible();
    await expect(page.getByText('Invoice 2041')).toBeVisible();
  });

  test('should show account balance or unavailable text in source picker', async ({ page }) => {
    // Navigate to payment entry
    await page.click('a:has-text("Pay & Transfer")');
    await page.click('button:has-text("Jamie Clarke")');
    await page.waitForURL('/payment-entry');

    // Check that source account select shows balance or unavailable text
    const sourceSelect = page.getByLabel('From');
    await expect(sourceSelect).toBeVisible();

    // Get the select options text
    const selectText = await sourceSelect.textContent();
    
    // Should show either a balance like "£1,248.36" or "Balance unavailable"
    // Should NOT show "£0.00" for unavailable balances
    expect(selectText).toContain('£');
    // Verify it doesn't show £0.00 for missing/unavailable balances
    if (selectText && selectText.includes('unavailable')) {
      expect(selectText).not.toContain('£0.00');
    }
  });

  test('should navigate back to payees list when back button clicked', async ({ page }) => {
    // Navigate to payment entry
    await page.click('a:has-text("Pay & Transfer")');
    await page.click('button:has-text("K Evans Lettings")');
    await page.waitForURL('/payment-entry');

    // Click back button
    await page.click('button:has-text("Back")');

    // Should return to payees list
    await page.waitForURL('/payees');
    await expect(page.locator('h1')).toContainText('Pay & Transfer');
    await expect(page.getByText('K Evans Lettings')).toBeVisible();
  });
});
