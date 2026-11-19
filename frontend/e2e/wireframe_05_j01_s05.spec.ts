import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 05 - Payment Entry and Approval (FR-005)', () => {
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

  test('should display payment entry form with payee and account details', async ({ page }) => {
    // Select a payee
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    
    // Continue to payment entry
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    // Verify payment entry page loads
    await expect(page.locator('h1')).toHaveText('Make a payment');
    // Target the payee panel specifically, not the notification that also mentions the payee
    await expect(page.locator('[aria-label*="Paying"] p').filter({ hasText: 'Jamie Clarke' })).toBeVisible();
    await expect(page.locator('text=04-00-04')).toBeVisible();
    
    // Verify from account is readonly
    const fromInput = page.locator('#from');
    await expect(fromInput).toHaveAttribute('readonly');
    await expect(fromInput).toHaveValue(/Current Account/);
    
    // Verify amount field
    const amountInput = page.locator('#amount');
    await expect(amountInput).toBeVisible();
    await expect(amountInput).toHaveValue('250.00');
    
    // Verify reference field
    const referenceInput = page.locator('#reference');
    await expect(referenceInput).toBeVisible();
  });

  test('should show inline error when amount exceeds balance', async ({ page }) => {
    // Select a payee and navigate to payment entry
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    // Enter amount exceeding balance
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('1500.00');
    
    // Click pay button
    await page.click('button:has-text("Pay £1,500.00")');
    
    // Wait for error message
    await expect(page.locator('text=/Payment amount exceeds/i')).toBeVisible();
    
    // Verify pay button is still enabled but error shown
    await expect(page.locator('button:has-text("Pay £1,500.00")')).toBeVisible();
  });

  test('should show approval modal with dynamic linking', async ({ page }) => {
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
    
    // Click pay button
    await page.click('button:has-text("Pay £50.00")');
    
    // Wait for approval modal (target the modal specifically)
    await expect(page.locator('[role="dialog"]')).toBeVisible();
    await expect(page.locator('[role="dialog"]').locator('h2:has-text("Approve with Face ID")')).toBeVisible();
    
    // Verify dynamic link summary shows payee and amount
    await expect(page.locator('text=Jamie Clarke')).toBeVisible();
    await expect(page.locator('text=£50.00')).toBeVisible();
    
    // Verify cancel and approve buttons present
    await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
    await expect(page.locator('button:has-text("Approve")')).toBeVisible();
  });

  test('should navigate to outcome page after successful approval', async ({ page }) => {
    // Select a payee and navigate to payment entry
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    // Enter valid payment details
    const amountInput = page.locator('#amount');
    await amountInput.clear();
    await amountInput.fill('50.00');
    
    // Click pay button
    await page.click('button:has-text("Pay £50.00")');
    
    // Wait for approval modal and approve (target the modal heading specifically, not the notification)
    await expect(page.locator('[role="dialog"] h2:has-text("Approve with Face ID")')).toBeVisible();
    await page.click('button:has-text("Approve")');
    
    // Wait for outcome page
    await page.waitForURL('**/payment/outcome');
    
    // Verify outcome page shows payment result
    await expect(page.locator('h1')).toHaveText(/Payment sent|Payment pending|Payment not sent/);
  });

  test('should enforce reference character limit of 18', async ({ page }) => {
    // Select a payee and navigate to payment entry
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    // Try to enter more than 18 characters
    const referenceInput = page.locator('#reference');
    await referenceInput.fill('123456789012345678901234567890');
    
    // Verify only 18 characters are accepted
    await expect(referenceInput).toHaveValue('123456789012345678');
  });

  test('should show info notification about Face ID approval', async ({ page }) => {
    // Select a payee and navigate to payment entry
    await page.click('button[role="radio"]:has-text("Jamie Clarke")');
    await page.click('button:has-text("Continue to payment")');
    await page.waitForURL('**/payment/entry');
    
    // Verify info notification present
    await expect(page.locator('text=You\'ll approve with Face ID')).toBeVisible();
    await expect(page.locator('text=/Your approval is tied to/i')).toBeVisible();
  });
});
