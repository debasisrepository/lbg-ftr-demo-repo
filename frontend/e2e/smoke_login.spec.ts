import { test, expect } from './_pipeline_guard';

/**
 * Smoke test: Login through the UI using the actual auth flow
 * 
 * This test verifies the frontend login infrastructure is correctly wired:
 * 1. The login page loads with passcode field
 * 2. Form submits passcode to the correct backend endpoint
 * 3. Successful login redirects to accounts page
 * 
 * Uses the actual device-based authentication flow:
 * - Device identifier: device-CUST-SYNTH-001-iOS
 * - Platform: iOS
 * - Passcode: Pass1234 (from seed data)
 */
test.describe('Smoke: Login Flow', () => {
  test('should render login page with form fields', async ({ page }) => {
    // Navigate to the app
    await page.goto('/');
    
    // Should redirect to login page if not authenticated
    await expect(page).toHaveURL(/\/login/);
    
    // Should show login form heading
    await expect(page.getByRole('heading', { name: /Sign in/i })).toBeVisible();
    
    // Should have passcode field
    const passcodeInput = page.locator('input[name="passcode"]');
    const submitButton = page.locator('button[type="submit"]');
    
    await expect(passcodeInput).toBeVisible();
    await expect(submitButton).toBeVisible();
    await expect(submitButton).toHaveText(/Sign in/i);
  });
  
  test('should login successfully with correct passcode and redirect to accounts', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    
    // Wait for form to be ready
    await page.waitForSelector('input[name="passcode"]');
    
    // Fill in passcode (the page uses device-based auth, not customer party ID)
    await page.locator('input[name="passcode"]').fill('Pass1234');
    
    // Listen for the API request
    const loginRequestPromise = page.waitForRequest(request => 
      request.url().includes('/api/v1/auth/login') && 
      request.method() === 'POST'
    );
    
    // Submit the form
    await page.locator('button[type="submit"]').click();
    
    // Verify the login request was made with correct credentials
    const loginRequest = await loginRequestPromise;
    expect(loginRequest.url()).toContain('/api/v1/auth/login');
    
    const requestBody = loginRequest.postDataJSON();
    expect(requestBody).toMatchObject({
      device_identifier: 'device-CUST-SYNTH-001-iOS',
      mobile_platform: 'iOS',
      passcode: 'Pass1234'
    });
    
    // Should redirect to accounts page after successful login
    await page.waitForURL(/\/accounts/, { timeout: 10000 });
    await expect(page).toHaveURL(/\/accounts/);
  });
  
  test('should show error message for incorrect passcode', async ({ page, apiGuard }) => {
    // Allow 401 for wrong password test
    apiGuard.allow(401, '/api/v1/auth/login');
    
    // Navigate to login
    await page.goto('/login');
    
    // Fill in wrong passcode
    await page.locator('input[name="passcode"]').fill('WrongPass');
    
    // Submit the form
    await page.locator('button[type="submit"]').click();
    
    // Should stay on login page
    await expect(page).toHaveURL(/\/login/);
    
    // Should show error message
    await expect(page.getByText(/Sign-in failed/i)).toBeVisible();
  });
});
