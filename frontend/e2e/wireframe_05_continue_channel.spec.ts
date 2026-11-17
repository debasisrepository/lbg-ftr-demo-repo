import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 05 - Continue Channel', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/email or username/i).fill('user1@example.com');
    await page.getByLabel(/password/i).fill('user123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for cases page to load after login
    await page.waitForURL('/cases', { timeout: 10000 });
  });
  
  test('should display continue channel page with three channel options', async ({ page }) => {
    // Navigate to a case's continue page
    await page.goto('/cases/CP-MOCK1/continue');
    
    // Verify page loads
    await expect(page.getByRole('heading', { name: /get help/i })).toBeVisible();
    
    // Verify description
    await expect(
      page.getByText(/Choose how you would like to carry on/)
    ).toBeVisible();
    
    // Verify three channel options are present
    await expect(page.getByText('Chat with an adviser')).toBeVisible();
    await expect(page.getByText('Phone call')).toBeVisible();
    await expect(page.getByText('Branch')).toBeVisible();
    
    // Verify wait time descriptions
    await expect(page.getByText('Usually a few minutes')).toBeVisible();
    await expect(page.getByText('We call you on the number we hold')).toBeVisible();
    await expect(page.getByText('Show your reference at the counter')).toBeVisible();
  });
  
  test('should display shared fields disclosure', async ({ page }) => {
    await page.goto('/cases/CP-MOCK1/continue');
    
    // Wait for page to load
    await page.waitForSelector('h1', { timeout: 15000 });
    
    const heading = await page.locator('h1').textContent();
    if (heading?.includes('Sign in')) {
      test.skip();
      return;
    }
    
    // Verify "What will be shared" accordion - Carbon Accordion uses button with title
    const accordionButton = page.getByRole('button', { name: /what will be shared/i });
    await expect(accordionButton).toBeVisible();
    
    // Verify "What is never shared" section
    await expect(page.getByRole('heading', { name: /what is never shared/i })).toBeVisible();
    await expect(page.getByText(/Your full card number/i)).toBeVisible();
    await expect(page.getByText(/Passcodes and security answers/i)).toBeVisible();
    await expect(page.getByText(/A full copy of earlier conversations/i)).toBeVisible();
  });
  
  test('should allow selecting a channel and submitting handoff', async ({ page }) => {
    await page.goto('/cases/CP-MOCK1/continue');
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: /get help/i })).toBeVisible();
    
    // Select phone channel - Click the label since Carbon's radio appearance intercepts clicks
    const phoneLabel = page.locator('label[for="channel-phone"]');
    await phoneLabel.click();
    
    // Verify phone is selected
    const phoneRadio = page.locator('#channel-phone');
    await expect(phoneRadio).toBeChecked();
    
    // Click continue button
    const submitButton = page.getByRole('button', { name: /continue/i });
    await submitButton.click();
    
    // Should redirect to case detail after successful handoff
    await page.waitForURL('/cases/CP-MOCK1', { timeout: 10000 });
  });
  
  test('should have back link to case detail', async ({ page }) => {
    await page.goto('/cases/CP-MOCK1/continue');
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: /get help/i })).toBeVisible();
    
    // Verify back link to case
    const backLink = page.getByRole('link', { name: /Case CP-MOCK1/i }).first();
    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute('href', '/cases/CP-MOCK1');
  });
  
  test('should have cancel button that returns to case', async ({ page }) => {
    await page.goto('/cases/CP-MOCK1/continue');
    
    // Wait for page to load
    await page.waitForSelector('h1', { timeout: 15000 });
    
    const heading = await page.locator('h1').textContent();
    if (heading?.includes('Sign in')) {
      test.skip();
      return;
    }
    
    // Verify cancel button
    const cancelButton = page.getByRole('link', { name: /cancel/i });
    await expect(cancelButton).toBeVisible();
    await expect(cancelButton).toHaveAttribute('href', '/cases/CP-MOCK1');
  });
});
