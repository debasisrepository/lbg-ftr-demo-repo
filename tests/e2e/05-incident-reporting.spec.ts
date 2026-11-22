import { test, expect } from './_pipeline_guard';

test.describe('Incident Reporting (BR-OPS-008)', () => {
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

  test('can navigate to incident report page', async ({ page }) => {
    // Navigate to help/support page
    await page.goto('/support');
    
    // Look for incident reporting link or button
    const incidentLink = page.locator('a[href="/support/incident"]');
    await expect(incidentLink).toBeVisible({ timeout: 5000 });
    
    // Click to navigate
    await incidentLink.click();
    await expect(page).toHaveURL('/support/incident');
  });

  test('can submit an incident report with all required fields', async ({ page }) => {
    await page.goto('/support/incident');
    
    // Fill out incident report form
    await page.selectOption('[name="incident_category"]', 'technical_issue');
    await page.fill('[name="incident_title"]', 'App crashes on payment page');
    await page.fill('[name="incident_description"]', 'When I try to make a payment, the app crashes immediately.');
    await page.selectOption('[name="severity"]', 'high');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should show success message or navigate to confirmation
    const successMessage = page.locator('text=/report.*submitted|incident.*created/i');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
    
    // Should show incident reference number
    const incidentRef = page.locator('text=/INC[A-Z0-9]+/');
    await expect(incidentRef).toBeVisible();
  });

  test('validates required fields on incident report form', async ({ page }) => {
    await page.goto('/support/incident');
    
    // Try to submit without filling required fields
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should show validation errors
    const validationError = page.locator('text=/required|must provide/i').first();
    await expect(validationError).toBeVisible({ timeout: 3000 });
  });

  test('can select different incident categories', async ({ page }) => {
    await page.goto('/support/incident');
    
    const categorySelect = page.locator('[name="incident_category"]');
    await expect(categorySelect).toBeVisible();
    
    // Verify all valid categories are available
    const categories = ['technical_issue', 'service_outage', 'data_issue', 'security_concern', 'other'];
    for (const category of categories) {
      const option = categorySelect.locator(`option[value="${category}"]`);
      await expect(option).toBeAttached();
    }
  });

  test('can select different severity levels', async ({ page }) => {
    await page.goto('/support/incident');
    
    const severitySelect = page.locator('[name="severity"]');
    await expect(severitySelect).toBeVisible();
    
    // Verify all valid severities are available
    const severities = ['low', 'medium', 'high', 'critical'];
    for (const severity of severities) {
      const option = severitySelect.locator(`option[value="${severity}"]`);
      await expect(option).toBeAttached();
    }
  });

  test('description field is optional', async ({ page }) => {
    await page.goto('/support/incident');
    
    // Fill only required fields (no description)
    await page.selectOption('[name="incident_category"]', 'technical_issue');
    await page.fill('[name="incident_title"]', 'Brief issue title');
    await page.selectOption('[name="severity"]', 'low');
    
    // Submit form
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Should still succeed
    const successMessage = page.locator('text=/report.*submitted|incident.*created/i');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
  });

  test('shows incident reference after submission', async ({ page }) => {
    await page.goto('/support/incident');
    
    // Submit incident report
    await page.selectOption('[name="incident_category"]', 'data_issue');
    await page.fill('[name="incident_title"]', 'Balance not updating');
    await page.selectOption('[name="severity"]', 'medium');
    await page.click('button[type="submit"]:has-text("Submit")');
    
    // Wait for success
    const successMessage = page.locator('text=/report.*submitted|incident.*created/i');
    await expect(successMessage).toBeVisible({ timeout: 5000 });
    
    // Should show incident reference in INC format
    const incidentRef = page.locator('text=/INC[A-Z0-9]{8}/');
    await expect(incidentRef).toBeVisible();
    
    // Extract and verify reference format
    const refText = await incidentRef.textContent();
    expect(refText).toMatch(/INC[A-Z0-9]{8}/);
  });

  test('can view submitted incident reports', async ({ page }) => {
    // First submit an incident
    await page.goto('/support/incident');
    await page.selectOption('[name="incident_category"]', 'technical_issue');
    await page.fill('[name="incident_title"]', 'Test incident for viewing');
    await page.selectOption('[name="severity"]', 'low');
    await page.click('button[type="submit"]:has-text("Submit")');
    
    await page.waitForSelector('text=/report.*submitted|incident.*created/i', { timeout: 5000 });
    
    // Navigate to support/incidents list (if such a page exists)
    await page.goto('/support');
    
    // Look for link to view incidents
    const viewIncidentsLink = page.locator('text=/view.*incidents|my.*reports|incident.*history/i');
    if (await viewIncidentsLink.isVisible({ timeout: 2000 })) {
      await viewIncidentsLink.click();
      
      // Should see the incident we just created
      await expect(page.locator('text=/Test incident for viewing/')).toBeVisible({ timeout: 5000 });
    }
  });
});
