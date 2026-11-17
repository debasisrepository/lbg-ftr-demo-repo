import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 04 - Colleague Hand-off Pack', () => {
  let caseId: string;
  let caseRef: string;

  test.beforeAll(async ({ browser }) => {
    // Create a real case by doing the customer flow
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Login as customer
    await page.goto('/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    await page.waitForURL('/');
    
    const customerToken = await page.evaluate(() => localStorage.getItem('access_token'));
    
    // Create resolve session
    const resolveResponse = await page.request.post('/api/v1/resolve', {
      headers: { 'Authorization': `Bearer ${customerToken}` },
      data: {
        message_text: 'Test case for colleague hand-off verification',
        status_context_shown: true,
      },
    });
    
    const resolveTurn = await resolveResponse.json();
    const sessionId = resolveTurn.session_id;
    
    // Request human help to create case
    const humanRequestResponse = await page.request.post(`/api/v1/resolve/${sessionId}/human-request`, {
      headers: { 'Authorization': `Bearer ${customerToken}` },
      data: {},
    });
    
    const humanRequestData = await humanRequestResponse.json();
    caseId = humanRequestData.case_id;
    caseRef = humanRequestData.case_ref;
    
    await context.close();
  });

  test('colleague can open case and see hand-off pack with transcript', async ({ page }) => {
    // Log in as colleague
    await page.goto('/login');
    await page.getByLabel('Email').fill('colleague@example.com');
    await page.getByLabel('Password').fill('colleague123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/');
    
    // Navigate to colleague cases (team worklist)
    await page.goto('/colleague/cases');
    
    // Navigate to the real case
    await page.goto(`/colleague/cases/${caseId}`);
    
    // Verify case header
    await expect(page.getByText(/colleague desktop/i)).toBeVisible();
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByText(caseRef).first()).toBeVisible();
    
    // Verify left column: one-screen summary
    await expect(page.getByRole('heading', { name: /one-screen summary/i })).toBeVisible();
    await expect(page.getByText('Status', { exact: true })).toBeVisible();
    await expect(page.getByText('Expected by', { exact: true })).toBeVisible();
    await expect(page.getByText(/why it came to us/i)).toBeVisible();
    await expect(page.getByText(/how it arrived/i)).toBeVisible();
    
    // Verify handling indicators
    await expect(page.getByRole('heading', { name: /handling indicators/i })).toBeVisible();
    
    // Verify team worklist
    await expect(page.getByRole('heading', { name: /my team's cases/i })).toBeVisible();
    
    // Verify center column: transcript
    await expect(page.getByRole('heading', { name: /conversation so far/i })).toBeVisible();
    await expect(page.getByRole('log')).toBeVisible();
    
    // Verify reply composer
    await expect(page.getByText(/reply to/i)).toBeVisible();
    await expect(page.getByRole('textbox', { name: /reply/i })).toBeVisible();
    await expect(page.locator('#vis')).toBeVisible();
    
    // Verify right column: evidence and timeline
    await expect(page.getByRole('heading', { name: /evidence/i })).toBeVisible();
    await expect(page.getByRole('heading', { name: /case history/i })).toBeVisible();
    
    // Verify action buttons
    await expect(page.getByRole('button', { name: /pick up this case/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /send reply/i })).toBeVisible();
  });
  
  test('colleague can post reply visible to customer', async ({ page }) => {
    // Log in as colleague
    await page.goto('/login');
    await page.getByLabel('Email').fill('colleague@example.com');
    await page.getByLabel('Password').fill('colleague123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    await expect(page).toHaveURL('/');
    
    // Navigate to the real case
    await page.goto(`/colleague/cases/${caseId}`);
    
    // Fill in reply
    const replyText = 'Hi, this is Priya from the fraud team. I\'ve reviewed your case and will update you shortly.';
    await page.getByRole('textbox', { name: /reply/i }).fill(replyText);
    
    // Ensure visibility is set to customer-visible
    await page.locator('#vis').selectOption('customer_and_colleague');
    
    // Send reply
    await page.getByRole('button', { name: /send reply/i }).click();
    
    // Verify reply appears in transcript (wait for API call)
    await expect(page.getByText(replyText)).toBeVisible({ timeout: 5000 });
  });
  
  test('colleague can save colleague-only note', async ({ page }) => {
    // Log in as colleague
    await page.goto('/login');
    await page.getByLabel('Email').fill('colleague@example.com');
    await page.getByLabel('Password').fill('colleague123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    await expect(page).toHaveURL('/');
    
    // Navigate to the real case
    await page.goto(`/colleague/cases/${caseId}`);
    
    // Fill in colleague-only note
    const noteText = 'Internal note: Customer seems distressed, handle with care.';
    await page.getByRole('textbox', { name: /reply/i }).fill(noteText);
    
    // Set visibility to colleague-only
    await page.locator('#vis').selectOption('colleague_only');
    
    // Save as note
    await page.getByRole('button', { name: /save.*colleague-only/i }).click();
    
    // Verify note appears in transcript
    await expect(page.getByText(noteText)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/colleague-only note/i)).toBeVisible();
  });
});
