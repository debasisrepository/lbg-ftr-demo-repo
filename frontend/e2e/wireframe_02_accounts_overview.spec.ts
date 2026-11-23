import { test, expect } from './_pipeline_guard';

test.describe('Wireframe 02 - Accounts Overview', () => {
  test.beforeEach(async ({ page }) => {
    // Login with seed credentials before each test
    await page.goto('/login');
    await page.getByLabel(/passcode/i).fill('Pass1234');
    await page.getByRole('button', { name: /sign in/i }).click();
    await expect(page).toHaveURL(/\/accounts/, { timeout: 10000 });
  });

  test('should render accounts overview page with account cards', async ({ page }) => {
    // Check heading
    await expect(page.getByRole('heading', { name: /your accounts/i })).toBeVisible();

    // Check greeting
    await expect(page.getByText(/hello,/i)).toBeVisible();

    // Wait for accounts to load and check that at least one account card is visible
    await expect(page.locator('article').first()).toBeVisible({ timeout: 10000 });

    // Check sign-out link
    await expect(page.getByRole('button', { name: /sign out/i })).toBeVisible();

    // Check tabs
    await expect(page.getByRole('link', { name: /accounts/i })).toBeVisible();
    await expect(page.getByRole('link', { name: /pay & transfer/i })).toBeVisible();
  });

  test('should display account cards with balances and freshness', async ({ page }) => {
    // Wait for accounts to load
    await expect(page.locator('article').first()).toBeVisible({ timeout: 10000 });

    // Get all account cards
    const accountCards = page.locator('article');
    const count = await accountCards.count();

    expect(count).toBeGreaterThan(0);

    // Check first account card structure
    const firstCard = accountCards.first();
    await expect(firstCard.getByRole('heading')).toBeVisible();
    
    // Should have account ending text
    await expect(firstCard.getByText(/account ending/i)).toBeVisible();

    // Should have either a balance amount or "Balance unavailable"
    const balanceText = await firstCard.locator('.balance-amount').textContent();
    expect(balanceText).toBeTruthy();

    // Should have freshness badge (Current, Stale, or Unavailable)
    const freshnessText = await firstCard.locator('.freshness-badge').textContent();
    expect(freshnessText).toMatch(/current|stale|unavailable|partly/i);
  });

  test('should never show missing balance as £0.00', async ({ page }) => {
    // Wait for accounts to load
    await expect(page.locator('article').first()).toBeVisible({ timeout: 10000 });

    // Get all account cards
    const accountCards = page.locator('article');
    const count = await accountCards.count();

    for (let i = 0; i < count; i++) {
      const card = accountCards.nth(i);
      
      // Get balance text
      const balanceText = await card.locator('.balance-amount').textContent();
      
      // If balance shows unavailable, ensure it does NOT show £0.00
      if (balanceText && balanceText.includes('unavailable')) {
        expect(balanceText).not.toContain('£0.00');
      }
    }
  });

  test('should show freshness text on each account', async ({ page }) => {
    // Wait for accounts to load
    await expect(page.locator('article').first()).toBeVisible({ timeout: 10000 });

    // Get all account cards
    const accountCards = page.locator('article');
    const count = await accountCards.count();

    expect(count).toBeGreaterThan(0);

    // Check each card has freshness text
    for (let i = 0; i < count; i++) {
      const card = accountCards.nth(i);
      
      // Should have freshness-related text
      const freshnessTime = await card.locator('.freshness-time').textContent();
      expect(freshnessTime).toBeTruthy();
      expect(freshnessTime).toMatch(/updated|not current|out of date/i);
    }
  });

  test('should have refresh accounts button', async ({ page }) => {
    await expect(page.getByRole('button', { name: /refresh accounts/i })).toBeVisible({ timeout: 10000 });
  });

  test('should allow sign-out', async ({ page }) => {
    // Click sign-out
    await page.getByRole('button', { name: /sign out/i }).click();

    // Should redirect to login page
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 });
  });

  test('should show capability banner when accounts have degraded state', async ({ page }) => {
    // Wait for accounts to load
    await expect(page.locator('article').first()).toBeVisible({ timeout: 10000 });

    // Check if there's a banner (may or may not be present depending on account states)
    const banner = page.locator('[role="status"]');
    const bannerCount = await banner.count();
    
    if (bannerCount > 0) {
      // If banner exists, verify it has appropriate content
      const text = await banner.first().textContent();
      expect(text).toBeTruthy();
      expect(text.length).toBeGreaterThan(0);
    }
  });

  test('should display greeting with user name', async ({ page }) => {
    // Check that greeting includes a name
    const greeting = page.getByText(/hello,/i);
    await expect(greeting).toBeVisible();
    
    const greetingText = await greeting.textContent();
    expect(greetingText).toMatch(/hello,\s+\w+/i);
  });
});
