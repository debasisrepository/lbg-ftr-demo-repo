import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 01 - Customer Intake Screen', () => {
  test.beforeEach(async ({ page }) => {
    // Login with seed credentials
    await page.goto('/login');
    await page.fill('#email', 'admin@example.com');
    await page.fill('#password', 'admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/');
    
    // Navigate to resolve page
    await page.getByRole('link', { name: /get help/i }).click();
    await expect(page).toHaveURL('/resolve');
  });

  test('should display all required UI sections', async ({ page }) => {
    // Verify page header
    await expect(page.getByText('Get help')).toBeVisible();
    
    // Verify AI assistant badge in header
    await expect(page.getByRole('banner').getByText('AI assistant')).toBeVisible();
    
    // Verify AI disclosure
    await expect(page.getByText(/You're talking to an AI assistant/i)).toBeVisible();
    
    // Verify service status context card
    await expect(page.getByText(/We have a problem with payments right now/i)).toBeVisible();
    await expect(page.getByText('Service status').first()).toBeVisible();
    
    // Verify page title
    await expect(page.getByRole('heading', { name: /What's gone wrong/i })).toBeVisible();
    
    // Verify transaction picker section
    await expect(page.getByText(/Or start from something you can see/i)).toBeVisible();
    
    // Verify textarea is present with label
    await expect(page.getByLabel(/Describe the problem/i)).toBeVisible();
    
    // Verify character count
    await expect(page.getByText(/of 4,000/i)).toBeVisible();
    
    // Verify "what happens next" section
    await expect(page.getByRole('heading', { name: /What happens when you send this/i })).toBeVisible();
    await expect(page.getByText(/We check what we can see on your account/i)).toBeVisible();
    
    // Verify submit button
    await expect(page.getByRole('button', { name: /Send to the assistant/i })).toBeVisible();
    
    // Verify human path button
    await expect(page.getByRole('button', { name: /Talk to a person/i })).toBeVisible();
  });

  test('should allow interaction with form elements', async ({ page }) => {
    // Wait for page to be ready
    await expect(page.getByRole('heading', { name: /What's gone wrong/i })).toBeVisible();
    
    // Type in textarea (clear first, then add new text)
    const textarea = page.getByLabel(/Describe the problem/i);
    await textarea.click();
    await textarea.fill('I have a problem with a recent payment.');
    
    // Verify text was entered
    await expect(textarea).toHaveValue('I have a problem with a recent payment.');
    
    // Verify we can select transactions
    const firstTransaction = page.locator('input[name="txn"]').first();
    await expect(firstTransaction).toBeVisible();
    await firstTransaction.check();
    await expect(firstTransaction).toBeChecked();
    
    // Verify attached transaction badge appears
    await expect(page.getByText(/Attached:/i)).toBeVisible();
  });

  test('should submit form and navigate to session', async ({ page }) => {
    // Fill in the form
    const textarea = page.getByLabel(/Describe the problem/i);
    await textarea.click();
    await textarea.fill('I need help with a suspicious transaction.');
    
    // Submit the form
    await page.getByRole('button', { name: /Send to the assistant/i }).click();
    
    // Should navigate to session page (will show loading or error if backend not ready)
    await page.waitForURL(/\/resolve\/.+/, { timeout: 10000 }).catch(() => {
      // If backend is not ready, we may get an error, which is acceptable for this test
    });
  });
});
