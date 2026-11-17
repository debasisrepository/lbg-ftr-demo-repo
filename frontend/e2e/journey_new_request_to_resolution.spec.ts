import { test, expect } from './_pipeline_guard';

/**
 * Journey: New request creation to resolution
 * 
 * Covers:
 * - Login as admin (colleague scope with customer_party_id)
 * - Create new case via POST /api/v1/cases with card_declined issue
 * - Assert case created with case_reference
 * - Navigate to case detail
 * - Assert status shows "In progress"
 * - Transition case to closed via POST /api/v1/cases/{case_reference}/transitions
 * - Navigate to case detail again
 * - Assert status shows "Closed" and outcome_summary is visible
 */
test('full journey: create case, view detail, transition to closed, verify outcome', async ({ page }) => {
  // Step 1: Login as admin (has colleague scope + customer_party_id for testing)
  await page.goto('/login');
  await expect(page.getByLabel(/email or username/i)).toHaveValue('admin@example.com');
  await expect(page.getByLabel(/password/i)).toHaveValue('admin123');
  await page.getByRole('button', { name: /sign in/i }).click();
  await expect(page).toHaveURL('/cases');

  // Step 2: Navigate to Report Issue page
  await page.goto('/report');
  await expect(page.getByRole('heading', { name: /report an issue/i })).toBeVisible();

  // Step 3: Create new case with card_declined issue
  // Select issue type
  const issueTypeSelect = page.locator('#issue-type');
  await issueTypeSelect.selectOption('card_declined');

  // Enter issue summary
  const summaryTextarea = page.locator('#issue-summary');
  await summaryTextarea.fill('My card was declined at the shop but I have funds available');

  // Submit form
  await page.getByRole('button', { name: /send/i }).click();

  // Step 4: Assert redirected to case detail with case_reference in URL
  await page.waitForURL(/\/cases\/CP-[A-Z0-9]{10}/, { timeout: 10000 });
  const currentUrl = page.url();
  const caseReferenceMatch = currentUrl.match(/\/cases\/(CP-[A-Z0-9]{10})/);
  expect(caseReferenceMatch).toBeTruthy();
  const caseReference = caseReferenceMatch![1];

  // Step 5: Assert case detail shows "In progress" status
  await expect(page.getByRole('heading', { name: new RegExp(caseReference, 'i') })).toBeVisible();
  
  // Status chip should show "In progress" (or similar initial state)
  const statusChip = page.locator('[data-testid="status-chip"]').first();
  await expect(statusChip).toContainText(/in progress|investigating|new/i);

  // Step 6: Transition case to closed (using API directly since UI doesn't expose transitions)
  // This simulates what a colleague would do from their interface
  const authToken = await page.evaluate(() => localStorage.getItem('auth_token'));
  
  const response = await page.request.post(`/api/v1/cases/${caseReference}/transitions`, {
    headers: {
      'Authorization': `Bearer ${authToken}`,
      'Content-Type': 'application/json',
    },
    data: {
      to_state: 'closed',
      basis_type: 'manual_update',
      basis_reference: 'e2e-test-closure',
      outcome_summary: 'Issue resolved - card unblocked and transaction completed successfully',
    },
  });
  
  expect(response.ok()).toBeTruthy();

  // Step 7: Refresh case detail page
  await page.reload();

  // Step 8: Assert status now shows "Closed"
  await expect(statusChip).toContainText(/closed|resolved/i);

  // Step 9: Assert outcome_summary is visible
  await expect(page.getByText(/issue resolved.*card unblocked/i)).toBeVisible();
});
