/**
 * E2E Test Helper Functions
 */
import { Page } from '@playwright/test';

/**
 * Log in via the UI form (tests the actual login flow)
 */
export async function loginViaForm(page: Page, passcode: string = 'Pass1234') {
  await page.goto('/login');
  await page.fill('input[type="password"]', passcode);
  await page.click('button[type="submit"]');
  
  // Wait for redirect to accounts
  await page.waitForURL('/accounts', { timeout: 10000 });
}
