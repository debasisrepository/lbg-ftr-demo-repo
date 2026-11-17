import { test, expect } from './_pipeline_guard';

const BACKEND_PORT = process.env.E2E_BACKEND_PORT || '9001';
const FRONTEND_PORT = process.env.E2E_FRONTEND_PORT || '5174';

test.describe('Wireframe 06: Protected Step', () => {
  test.beforeEach(async ({ page }) => {
    // Login first with correct seed credentials
    await page.goto('/login');
    await page.getByLabel(/email or username/i).fill('user1@example.com');
    await page.getByLabel(/password/i).fill('user123');
    await page.getByRole('button', { name: /sign in/i }).click();
    
    // Wait for redirect to cases
    await page.waitForURL('/cases', { timeout: 10000 });
  });

  test('displays protected action with 3-step progress', async ({ page }) => {
    // Use the seeded protected action (pending_sca) - UUID(int=14001)
    const actionId = '00000000-0000-0000-0000-0000000036b1';
    await page.goto(`/cases/CP-MOCK1/actions/${actionId}`);
    
    // Wait for page to load
    await expect(page.getByRole('heading', { name: 'Protected action' })).toBeVisible();
    
    // Check for 3-step progress indicator
    await expect(page.getByText('1. Choose the change')).toBeVisible();
    await expect(page.getByText('2. Security check')).toBeVisible();
    await expect(page.getByText('3. Change applied')).toBeVisible();
  });

  test('shows SCA prompt when action is pending_sca', async ({ page }) => {
    const actionId = '00000000-0000-0000-0000-0000000036b1';
    await page.goto(`/cases/CP-MOCK1/actions/${actionId}`);
    
    await expect(page.getByRole('heading', { name: 'Protected action' })).toBeVisible();
    
    // Check for SCA prompt panel
    await expect(page.getByRole('heading', { name: 'Security check required' })).toBeVisible();
    await expect(page.getByText(/Confirm in your banking app/)).toBeVisible();
    
    // Check for action buttons
    await expect(page.getByRole('button', { name: /Confirm it is me/ })).toBeVisible();
    await expect(page.getByRole('button', { name: /Cancel/ })).toBeVisible();
  });

  test('shows authenticating modal when SCA starts', async ({ page }) => {
    const actionId = '00000000-0000-0000-0000-0000000036b1';
    await page.goto(`/cases/CP-MOCK1/actions/${actionId}`);
    
    await expect(page.getByRole('heading', { name: 'Protected action' })).toBeVisible();
    
    // Click "Confirm it is me" button
    await page.getByRole('button', { name: /Confirm it is me/ }).click();
    
    // Check for modal with authenticating message
    await expect(page.getByRole('heading', { name: 'Authenticating...' })).toBeVisible();
    await expect(page.getByText(/Waiting for authentication/)).toBeVisible();
  });

  test('handles action not found gracefully', async ({ page, apiGuard }) => {
    apiGuard.allow(404, '/actions/');
    const nonExistentActionId = '00000000-0000-0000-0000-999999999999';
    await page.goto(`/cases/CP-MOCK1/actions/${nonExistentActionId}`);
    
    // Should show error message
    await expect(page.getByText('Failed to load action')).toBeVisible();
  });

  test('provides back link to case detail', async ({ page }) => {
    const actionId = '00000000-0000-0000-0000-0000000036b1';
    await page.goto(`/cases/CP-MOCK1/actions/${actionId}`);
    
    await expect(page.getByRole('heading', { name: 'Protected action' })).toBeVisible();
    
    // Check for back link
    const backLink = page.locator('a.back-link');
    await expect(backLink).toBeVisible();
    await expect(backLink).toContainText('Case CP-MOCK1');
    
    // Click back link and verify navigation
    await backLink.click();
    await page.waitForURL('/cases/CP-MOCK1', { timeout: 10000 });
  });
});
