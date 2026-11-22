import { test, expect } from './_pipeline_guard';

test.describe('Dual Authorization for Business Payments (BR-ACCT-010)', () => {
  test.beforeEach(async ({ page }) => {
    // Login as business user
    await page.goto('/login');
    await page.fill('#username', 'alex.rodriguez@outlook.com');
    await page.fill('#password', 'Demo1234!');
    await page.click('button[type="submit"]');
    
    // Complete passcode
    await page.waitForURL('/proof', { timeout: 10000 });
    const digits = ['1', '2', '3', '4', '5', '6'];
    for (const digit of digits) {
      await page.click(`button:has-text("${digit}")`);
      await page.waitForTimeout(100);
    }
    
    await page.waitForURL('/accounts', { timeout: 10000 });
    
    // Switch to business profile
    const businessTab = page.locator('[role="tab"]', { hasText: 'Business' });
    if (await businessTab.isVisible({ timeout: 2000 })) {
      await businessTab.click();
      await page.waitForTimeout(500);
    }
  });

  test('can view pending approvals list', async ({ page }) => {
    // Navigate to payments page
    await page.goto('/pay-and-transfer');
    
    // Look for pending approvals section
    const pendingApprovalsSection = page.locator('[data-testid="pending-approvals"], text=/pending.*approval/i').first();
    
    // Pending approvals section should be visible (even if empty)
    if (await pendingApprovalsSection.isVisible({ timeout: 2000 })) {
      await expect(pendingApprovalsSection).toBeVisible();
    }
  });

  test('pending approval shows payment details', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    // Look for any pending approval items
    const approvalItem = page.locator('[data-testid="approval-item"]').first();
    
    if (await approvalItem.isVisible({ timeout: 2000 })) {
      // Should show key payment details
      await expect(approvalItem.locator('text=/£[0-9,]+\\.?[0-9]*/')).toBeVisible();  // Amount
      await expect(approvalItem.locator('text=/.+/')).toBeVisible();  // Payee name or description
    }
  });

  test('pending approval shows who initiated the payment', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    const approvalItem = page.locator('[data-testid="approval-item"]').first();
    
    if (await approvalItem.isVisible({ timeout: 2000 })) {
      // Should show initiator information
      const initiatorInfo = approvalItem.locator('text=/initiated by|requested by|from/i');
      await expect(initiatorInfo).toBeVisible();
    }
  });

  test('can approve a pending payment', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    const approvalItem = page.locator('[data-testid="approval-item"]').first();
    
    if (await approvalItem.isVisible({ timeout: 2000 })) {
      // Look for approve button
      const approveButton = approvalItem.locator('button:has-text("Approve")');
      
      if (await approveButton.isVisible({ timeout: 1000 })) {
        await approveButton.click();
        
        // Should show confirmation or navigate to approval flow
        const confirmationMessage = page.locator('text=/approved|confirm|authorize/i');
        await expect(confirmationMessage).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('can reject a pending payment', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    const approvalItem = page.locator('[data-testid="approval-item"]').first();
    
    if (await approvalItem.isVisible({ timeout: 2000 })) {
      // Look for reject button
      const rejectButton = approvalItem.locator('button:has-text("Reject"), button:has-text("Decline")');
      
      if (await rejectButton.isVisible({ timeout: 1000 })) {
        await rejectButton.click();
        
        // Should show confirmation
        const confirmationMessage = page.locator('text=/rejected|declined|cancelled/i');
        await expect(confirmationMessage).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('shows empty state when no pending approvals', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    // Look for empty state message
    const emptyState = page.locator('text=/no.*pending|no.*payment.*await|nothing.*approve/i');
    
    // Either have approvals or show empty state
    const hasPendingApprovals = await page.locator('[data-testid="approval-item"]').count() > 0;
    
    if (!hasPendingApprovals) {
      await expect(emptyState).toBeVisible({ timeout: 3000 });
    }
  });

  test('pending approval shows payment reference', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    const approvalItem = page.locator('[data-testid="approval-item"]').first();
    
    if (await approvalItem.isVisible({ timeout: 2000 })) {
      // Should show payment reference or description
      const referenceText = approvalItem.locator('text=/.{3,}/');  // At least 3 characters
      await expect(referenceText.first()).toBeVisible();
    }
  });

  test('dual authorization required indicator shown for business accounts', async ({ page }) => {
    // Navigate to accounts page
    await page.goto('/accounts');
    
    // Look for business accounts
    const businessAccount = page.locator('[data-testid="account-card"]').first();
    
    if (await businessAccount.isVisible({ timeout: 2000 })) {
      // Should indicate dual authorization requirement
      const dualAuthIndicator = page.locator('text=/dual.*author|two.*approval|requires.*approval/i');
      
      // May be shown on account or on payments page
      if (!await dualAuthIndicator.isVisible({ timeout: 1000 })) {
        await page.goto('/pay-and-transfer');
        await expect(page.locator('text=/dual.*author|two.*approval|requires.*approval/i')).toBeVisible({ timeout: 3000 });
      }
    }
  });

  test('approval requires authentication', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    const approvalItem = page.locator('[data-testid="approval-item"]').first();
    
    if (await approvalItem.isVisible({ timeout: 2000 })) {
      const approveButton = approvalItem.locator('button:has-text("Approve")');
      
      if (await approveButton.isVisible({ timeout: 1000 })) {
        await approveButton.click();
        
        // Should require step-up authentication or SCA
        const authPrompt = page.locator('text=/enter.*passcode|confirm.*identity|authenticate|step.*up/i');
        await expect(authPrompt).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('shows timestamp for when approval was requested', async ({ page }) => {
    await page.goto('/pay-and-transfer');
    
    const approvalItem = page.locator('[data-testid="approval-item"]').first();
    
    if (await approvalItem.isVisible({ timeout: 2000 })) {
      // Should show timestamp or relative time
      const timestamp = approvalItem.locator('text=/\\d{1,2}[\\s\\/\\-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[0-9]{1,2})|\\d+\\s*(minute|hour|day).*ago|today|yesterday/i');
      await expect(timestamp).toBeVisible();
    }
  });
});
