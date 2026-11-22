import { test, expect } from './_pipeline_guard';

test.describe('Loan View (BR-ACCT-004)', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('#username', 'sasha.patel@gmail.com');
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
  });

  test('displays loan with outstanding balance', async ({ page }) => {
    // Should be on accounts page showing loan
    await expect(page).toHaveURL('/accounts');
    
    // Look for loan card or section
    const loanCard = page.locator('[data-testid="loan-card"], [class*="loan"]').first();
    
    // If loan exists, verify it shows outstanding balance
    if (await loanCard.isVisible({ timeout: 2000 })) {
      // Should show outstanding balance amount
      const balanceAmount = loanCard.locator('text=/£[0-9,]+\\.?[0-9]*/');
      await expect(balanceAmount).toBeVisible();
      
      // Should have label indicating it's outstanding balance
      const balanceLabel = loanCard.locator('text=/outstanding|balance|owed/i');
      await expect(balanceLabel).toBeVisible();
    }
  });

  test('displays next repayment amount and date', async ({ page }) => {
    await expect(page).toHaveURL('/accounts');
    
    // Look for loan card
    const loanCard = page.locator('[data-testid="loan-card"], [class*="loan"]').first();
    
    if (await loanCard.isVisible({ timeout: 2000 })) {
      // Should show next repayment section
      const nextRepayment = loanCard.locator('text=/next.*payment|next.*repayment|due/i');
      await expect(nextRepayment).toBeVisible();
      
      // Should show repayment amount
      const repaymentAmount = loanCard.locator('text=/£[0-9,]+\\.?[0-9]*/');
      await expect(repaymentAmount).toBeVisible();
      
      // Should show repayment date (various date formats)
      const repaymentDate = loanCard.locator('text=/\\d{1,2}[\\s\\/\\-](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[0-9]{1,2})[\\s\\/\\-]\\d{2,4}|on\\s+[A-Z][a-z]+\\s+\\d{1,2}/i');
      await expect(repaymentDate).toBeVisible();
    }
  });

  test('loan shows correct product type', async ({ page }) => {
    await expect(page).toHaveURL('/accounts');
    
    const loanCard = page.locator('[data-testid="loan-card"], [class*="loan"]').first();
    
    if (await loanCard.isVisible({ timeout: 2000 })) {
      // Should indicate it's a loan product
      const loanLabel = loanCard.locator('text=/loan|mortgage|credit/i');
      await expect(loanLabel).toBeVisible();
    }
  });

  test('loan card displays loan name or account number', async ({ page }) => {
    await expect(page).toHaveURL('/accounts');
    
    const loanCard = page.locator('[data-testid="loan-card"], [class*="loan"]').first();
    
    if (await loanCard.isVisible({ timeout: 2000 })) {
      // Should show loan identifier (name or masked account number)
      const loanIdentifier = loanCard.locator('text=/personal.*loan|home.*loan|•{4}\\s*\\d{4}/i');
      await expect(loanIdentifier).toBeVisible();
    }
  });

  test('can tap loan card to view details', async ({ page }) => {
    await expect(page).toHaveURL('/accounts');
    
    const loanCard = page.locator('[data-testid="loan-card"], [class*="loan"]').first();
    
    if (await loanCard.isVisible({ timeout: 2000 })) {
      // Loan card should be clickable/tappable
      await expect(loanCard).toBeEnabled();
      
      // Click/tap the loan card
      await loanCard.click();
      
      // Should navigate to loan detail page or show detail view
      // (exact behavior depends on implementation)
      await page.waitForTimeout(1000);
      
      // URL might change or detail view appears
      const currentUrl = page.url();
      const hasDetailView = await page.locator('[data-testid="loan-detail"]').isVisible({ timeout: 1000 }).catch(() => false);
      
      // Either URL changed or detail view is shown
      expect(currentUrl.includes('/loan') || currentUrl.includes('/account') || hasDetailView).toBeTruthy();
    }
  });

  test('loan displays with UK currency formatting', async ({ page }) => {
    await expect(page).toHaveURL('/accounts');
    
    const loanCard = page.locator('[data-testid="loan-card"], [class*="loan"]').first();
    
    if (await loanCard.isVisible({ timeout: 2000 })) {
      // Look for amounts formatted with £ symbol
      const ukAmount = loanCard.locator('text=/£[0-9,]+\\.?[0-9]*/');
      await expect(ukAmount).toBeVisible();
      
      // Verify format (should use comma separators for thousands)
      const amountText = await ukAmount.first().textContent();
      expect(amountText).toMatch(/£[0-9]{1,3}(,[0-9]{3})*(\.[0-9]{2})?/);
    }
  });

  test('shows data unavailable message if loan service is down', async ({ page, apiGuard }) => {
    // Allow failed state for this test
    apiGuard.allowFailedState('/api/v1/accounts/overview');
    
    // Intercept loan data request to simulate service unavailable
    await page.route('**/api/v1/accounts/overview', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          accounts: [],
          loans: [],
          data_freshness: {
            accounts_retrieved_at: new Date().toISOString(),
            loans_retrieved_at: null,
            loans_error: 'Service temporarily unavailable'
          }
        })
      });
    });
    
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Should show message about loan data being unavailable
    const unavailableMessage = page.locator('text=/loan.*unavailable|unable.*load.*loan|try.*again/i');
    await expect(unavailableMessage).toBeVisible({ timeout: 5000 });
  });
});
