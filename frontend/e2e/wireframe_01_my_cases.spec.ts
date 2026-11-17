import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 01: My Cases', () => {
  test.beforeEach(async ({ page }) => {
    // Login with seed credentials
    await page.goto('/login');
    await page.locator('#username').fill('admin@example.com');
    await page.locator('#password').fill('admin123');
    await page.locator('button[type="submit"]').click();
    
    // Wait for redirect to cases page
    await page.waitForURL('/cases', { timeout: 15000 });
    
    // Wait for the page content to load
    await page.waitForSelector('h1', { timeout: 10000 });
  });

  test('displays My Cases page with heading', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'My Cases', level: 1 })).toBeVisible();
  });

  test('displays Report a new issue button', async ({ page }) => {
    const button = page.getByRole('link', { name: /Report a new issue/i });
    await expect(button).toBeVisible();
  });

  test('displays Show closed Cases toggle', async ({ page }) => {
    await expect(page.locator('text=Show closed Cases')).toBeVisible();
    const toggle = page.getByRole('switch');
    await expect(toggle).toBeVisible();
  });
});
