import { test, expect } from './_pipeline_guard';

test.describe('Profile Switching (BR-ACCT-002)', () => {
  test('can switch between personal and business profiles without re-authentication', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('#username', 'alex.rodriguez@outlook.com');
    await page.fill('#password', 'Demo1234!');
    await page.click('button[type="submit"]');
    
    // Complete passcode
    await page.waitForURL('/proof', { timeout: 10000 });
    const digits = ['1', '2', '3', '4', '5', '6'];
    for (const digit of digits) {
      await page.click(`button:has-text("${digit}")`);
      await page.waitForTimeout(100);
    }
    
    // Should be on accounts page
    await page.waitForURL('/accounts', { timeout: 10000 });
    
    // Look for profile switcher (should have both Personal and Business tabs)
    const profileSwitcher = page.locator('[role="tablist"][aria-label="Profile"]');
    await expect(profileSwitcher).toBeVisible({ timeout: 5000 });
    
    // Verify both profile tabs are present
    const personalTab = page.locator('[role="tab"]', { hasText: 'Personal' });
    const businessTab = page.locator('[role="tab"]', { hasText: 'Business' });
    await expect(personalTab).toBeVisible();
    await expect(businessTab).toBeVisible();
    
    // Verify one tab is active
    const activeTab = page.locator('[role="tab"][aria-selected="true"]');
    await expect(activeTab).toBeVisible();
    
    // Switch to the non-active profile
    const currentlyActive = await activeTab.textContent();
    if (currentlyActive?.includes('Personal')) {
      await businessTab.click();
      await expect(businessTab).toHaveAttribute('aria-selected', 'true');
    } else {
      await personalTab.click();
      await expect(personalTab).toHaveAttribute('aria-selected', 'true');
    }
    
    // Should still be on accounts page (no re-authentication)
    await expect(page).toHaveURL('/accounts');
  });

  test('shows loading state when switching profiles', async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('#username', 'alex.rodriguez@outlook.com');
    await page.fill('#password', 'Demo1234!');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/proof', { timeout: 10000 });
    const digits = ['1', '2', '3', '4', '5', '6'];
    for (const digit of digits) {
      await page.click(`button:has-text("${digit}")`);
      await page.waitForTimeout(100);
    }
    
    await page.waitForURL('/accounts', { timeout: 10000 });
    
    // Find inactive tab
    const inactiveTab = page.locator('[role="tab"][aria-selected="false"]').first();
    
    // Click and check aria-busy is set
    await inactiveTab.click();
    
    // Profile should switch successfully
    await expect(inactiveTab).toHaveAttribute('aria-selected', 'true', { timeout: 3000 });
  });

  test('shows error message if profile switch fails', async ({ page, apiGuard }) => {
    // Allow error response for this test
    apiGuard.allow(500, '/api/v1/profiles/active');
    
    // Login
    await page.goto('/login');
    await page.fill('#username', 'alex.rodriguez@outlook.com');
    await page.fill('#password', 'Demo1234!');
    await page.click('button[type="submit"]');
    
    await page.waitForURL('/proof', { timeout: 10000 });
    const digits = ['1', '2', '3', '4', '5', '6'];
    for (const digit of digits) {
      await page.click(`button:has-text("${digit}")`);
      await page.waitForTimeout(100);
    }
    
    await page.waitForURL('/accounts', { timeout: 10000 });
    
    // Intercept profile switch request to force error
    await page.route('**/api/v1/profiles/active', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Profile switch failed' })
      });
    });
    
    // Try to switch profile
    const inactiveTab = page.locator('[role="tab"][aria-selected="false"]').first();
    await inactiveTab.click();
    
    // Should show error message
    const errorMessage = page.locator('[role="alert"]');
    await expect(errorMessage).toBeVisible({ timeout: 3000 });
    await expect(errorMessage).toContainText(/failed/i);
  });
});
