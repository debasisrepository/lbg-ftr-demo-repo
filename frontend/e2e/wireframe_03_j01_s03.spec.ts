import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 03 - Case Confirmation', () => {
  test('customer sees case confirmation after requesting human help', async ({ page }) => {
    test.setTimeout(60000); // Increase timeout for this integration test
    // Log in as customer
    await page.goto('/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/');
    
    // Navigate to resolve page
    await page.goto('/resolve');
    
    // Start resolve session - the textarea has label "Describe the problem"
    await page.getByLabel(/describe the problem/i).fill('I have an unrecognised payment on my card for £89.99');
    await page.getByRole('button', { name: /send to the assistant/i }).click();
    
    // Wait for session to be created and response
    await expect(page.getByText(/assistant/i).first()).toBeVisible({ timeout: 10000 });
    
    // Request human help
    const humanButton = page.getByRole('button', { name: /talk to a person/i });
    await expect(humanButton).toBeVisible({ timeout: 5000 });
    await humanButton.click();
      
    // Wait for case creation and redirect to confirmation
    await expect(page).toHaveURL(/\/case-confirmation/, { timeout: 10000 });
    
    // Verify hero section
    await expect(page.getByRole('heading', { name: /we've passed this to our team/i })).toBeVisible();
    await expect(page.getByText(/you asked to talk to a person/i)).toBeVisible();
    
    // Verify three-panel section
    await expect(page.getByRole('heading', { name: /what you need to know/i })).toBeVisible();
    await expect(page.getByText(/who has it/i)).toBeVisible();
    await expect(page.getByText(/next update expected by/i)).toBeVisible();
    await expect(page.getByText(/what we know/i)).toBeVisible();
    
    // Verify checklist
    await expect(page.getByRole('heading', { name: /what we've already sent to the team/i })).toBeVisible();
    await expect(page.getByText(/what you told us, in your own words/i)).toBeVisible();
    
    // Verify My Cases section
    await expect(page.getByRole('heading', { name: /now in my cases/i })).toBeVisible();
    await expect(page.getByText(/case cp-/i).first()).toBeVisible();
    
    // Verify action buttons
    await expect(page.getByRole('button', { name: /open the conversation/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /i'd like a call-back/i })).toBeVisible();
  });
});
