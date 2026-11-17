import { Page } from '@playwright/test';

export async function loginViaAPI(page: Page, username: string, password: string) {
  // Login via API to save time in non-login tests
  const response = await page.request.post('http://127.0.0.1:9100/api/v1/auth/login', {
    data: { username, password, channel: 'mobile_app' }
  });
  
  const data = await response.json();
  
  // Navigate to a page first to establish context
  await page.goto('/login');
  
  // Store token in localStorage (matching the app's storage key from shared_config.json)
  await page.evaluate((token) => {
    localStorage.setItem('auth_token', token);
  }, data.access_token);
  
  // Also store user data if needed
  await page.evaluate((user) => {
    localStorage.setItem('user', JSON.stringify(user));
  }, data.user);
}
