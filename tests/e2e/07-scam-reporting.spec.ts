import { test, expect } from './_pipeline_guard';

test.describe('Scam Reporting (CMP-RES-04, CMP-RES-05)', () => {
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

  test('can navigate to scam report page', async ({ page }) => {
    // Navigate to support page
    await page.goto('/support');
    
    // Look for scam reporting link
    const scamReportLink = page.locator('a[href="/support/scam-report"]');
    await expect(scamReportLink).toBeVisible({ timeout: 5000 });
    
    await scamReportLink.click();
    await expect(page).toHaveURL('/support/scam-report');
  });

  test('can submit scam report with required fields', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    // Fill out scam report form
    await page.selectOption('[name="claim_type"]', 'scam');
    await page.fill('[name="claim_description"]', 'I received a text message claiming to be from the bank asking me to verify my account details.');
    await page.fill('[name="amount_minor"]', '5000');
    await page.fill('[name="transaction_date"]', '2026-11-15');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should show success message
    const successMessage = page.locator('text=/claim.*submitted|report.*received/i');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
    
    // Should show claim reference
    const claimRef = page.locator('text=/SCM[A-Z0-9]+/');
    await expect(claimRef).toBeVisible();
  });

  test('can submit unauthorised payment report', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    // Fill out unauthorised payment report
    await page.selectOption('[name="claim_type"]', 'unauthorised_transaction');
    await page.fill('[name="claim_description"]', 'I did not authorize this payment. I did not make this transaction and do not recognize the payee.');
    await page.fill('[name="amount_minor"]', '15000');
    await page.fill('[name="transaction_date"]', '2026-11-20');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should show success message
    const successMessage = page.locator('text=/claim.*submitted|report.*received/i');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
  });

  test('displays reimbursement timeline after submission', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    // Submit scam report
    await page.selectOption('[name="claim_type"]', 'scam');
    await page.fill('[name="claim_description"]', 'Scam report for timeline test');
    await page.fill('[name="amount_minor"]', '10000');
    await page.fill('[name="transaction_date"]', '2026-11-18');
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Wait for success
    await page.waitForSelector('text=/claim.*submitted|report.*received/i', { timeout: 5000 });
    
    // Should show reimbursement timeline
    const timeline = page.locator('[data-testid="reimbursement-timeline"], [class*="timeline"]');
    await expect(timeline).toBeVisible({ timeout: 3000 });
    
    // Timeline should show key stages
    await expect(timeline.locator('text=/review|investigation|decision|reimbursement/i')).toBeVisible();
  });

  test('reimbursement timeline shows expected timeframes', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    // Submit report
    await page.selectOption('[name="claim_type"]', 'unauthorised_transaction');
    await page.fill('[name="claim_description"]', 'Timeline test report');
    await page.fill('[name="amount_minor"]', '20000');
    await page.fill('[name="transaction_date"]', '2026-11-19');
    await page.click('button[type="submit"]:has-text("Submit")');
    
    await page.waitForSelector('text=/claim.*submitted|report.*received/i', { timeout: 5000 });
    
    // Look for timeline with duration indicators
    const timeline = page.locator('[data-testid="reimbursement-timeline"], [class*="timeline"]');
    
    // Should mention timeframes (days, weeks, or business days)
    const timeframeText = timeline.locator('text=/\\d+\\s*(day|week|business day)/i');
    await expect(timeframeText.first()).toBeVisible({ timeout: 3000 });
  });

  test('validates required fields on scam report form', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    // Try to submit without filling required fields
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should show validation errors
    const validationError = page.locator('text=/required|must provide/i').first();
    await expect(validationError).toBeVisible({ timeout: 3000 });
  });

  test('amount must be positive number', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    await page.selectOption('[name="claim_type"]', 'scam');
    await page.fill('[name="claim_description"]', 'Test report');
    await page.fill('[name="amount_minor"]', '-100');
    await page.fill('[name="transaction_date"]', '2026-11-15');
    
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should show validation error for negative amount
    const validationError = page.locator('text=/positive|greater than|invalid.*amount/i');
    await expect(validationError).toBeVisible({ timeout: 3000 });
  });

  test('transaction date cannot be in the future', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    await page.selectOption('[name="claim_type"]', 'scam');
    await page.fill('[name="claim_description"]', 'Test report');
    await page.fill('[name="amount_minor"]', '5000');
    
    // Set future date
    const futureDate = new Date();
    futureDate.setDate(futureDate.getDate() + 7);
    const futureDateStr = futureDate.toISOString().split('T')[0];
    await page.fill('[name="transaction_date"]', futureDateStr);
    
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should show validation error
    const validationError = page.locator('text=/future|cannot be after|invalid.*date/i');
    await expect(validationError).toBeVisible({ timeout: 3000 });
  });

  test('shows claim reference in correct format', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    await page.selectOption('[name="claim_type"]', 'scam');
    await page.fill('[name="claim_description"]', 'Reference format test');
    await page.fill('[name="amount_minor"]', '8000');
    await page.fill('[name="transaction_date"]', '2026-11-16');
    await page.click('button[type="submit"]:has-text("Submit")');
    
    await page.waitForSelector('text=/claim.*submitted/i', { timeout: 5000 });
    
    // Should show claim reference in SCM format
    const claimRef = page.locator('text=/SCM[A-Z0-9]{8}/');
    await expect(claimRef).toBeVisible();
    
    // Extract and verify format
    const refText = await claimRef.textContent();
    expect(refText).toMatch(/SCM[A-Z0-9]{8}/);
  });

  test('reimbursement timeline is in plain English', async ({ page }) => {
    await page.goto('/support/scam-report');
    
    await page.selectOption('[name="claim_type"]', 'scam');
    await page.fill('[name="claim_description"]', 'Plain English test');
    await page.fill('[name="amount_minor"]', '12000');
    await page.fill('[name="transaction_date"]', '2026-11-17');
    await page.click('button[type="submit"]:has-text("Submit")');
    
    await page.waitForSelector('text=/claim.*submitted/i', { timeout: 5000 });
    
    const timeline = page.locator('[data-testid="reimbursement-timeline"], [class*="timeline"]');
    await expect(timeline).toBeVisible();
    
    // Timeline text should be clear and avoid jargon
    const timelineText = await timeline.textContent();
    
    // Should use plain language (checking for clear terms)
    const hasPlainLanguage = 
      timelineText?.toLowerCase().includes('we') || 
      timelineText?.toLowerCase().includes('you') ||
      timelineText?.toLowerCase().includes('review') ||
      timelineText?.toLowerCase().includes('decision');
    
    expect(hasPlainLanguage).toBeTruthy();
  });
});
