/**
 * E2E test for wireframe_01: Sign in (FR-001)
 * Tests the complete sign-in flow with seed credentials
 */

import { test, expect } from '@playwright/test'

test.describe('Wireframe 01: Sign In', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage before each test
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
  })

  test('logs in with valid credentials and advances to proof screen', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login')

    // Wait for page to load
    await expect(page.locator('h2:has-text("Login")')).toBeVisible()

    // Enter seed credentials
    await page.fill('input[type="text"]#username', 'sasha.patel@gmail.com')
    await page.fill('input[type="password"]#password', 'Demo1234!')

    // Click continue
    await page.click('button:has-text("Continue")')

    // Should navigate to proof screen
    await expect(page).toHaveURL(/\/proof/)
    
    // Should show passcode entry screen
    await expect(page.locator('h2:has-text("Enter your passcode")')).toBeVisible()
  })

  test('shows validation errors for empty fields', async ({ page }) => {
    await page.goto('/login')

    // Click continue without entering credentials
    await page.click('button:has-text("Continue")')

    // Should show validation errors
    await expect(page.locator('text=/Error: Enter your username/i')).toBeVisible()
    await expect(page.locator('text=/Error: Enter your password/i')).toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL(/\/login/)
  })

  test('shows validation error for only username empty', async ({ page }) => {
    await page.goto('/login')

    // Enter only password
    await page.fill('input[type="password"]#password', 'Demo1234!')
    await page.click('button:has-text("Continue")')

    // Should show validation error for username only
    await expect(page.locator('text=/Error: Enter your username/i')).toBeVisible()
    await expect(page.locator('text=/Error: Enter your password/i')).not.toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL(/\/login/)
  })

  test('shows validation error for only password empty', async ({ page }) => {
    await page.goto('/login')

    // Enter only username
    await page.fill('input[type="text"]#username', 'sasha.patel@gmail.com')
    await page.click('button:has-text("Continue")')

    // Should show validation error for password only
    await expect(page.locator('text=/Error: Enter your password/i')).toBeVisible()
    await expect(page.locator('text=/Error: Enter your username/i')).not.toBeVisible()

    // Should not navigate away
    await expect(page).toHaveURL(/\/login/)
  })

  test('shows generic error message for invalid credentials', async ({ page }) => {
    await page.goto('/login')

    // Enter invalid credentials
    await page.fill('input[type="text"]#username', 'wrong@example.com')
    await page.fill('input[type="password"]#password', 'WrongPassword123!')

    // Click continue
    await page.click('button:has-text("Continue")')

    // Should show generic error message (not revealing which credential was wrong)
    await expect(
      page.locator('text=/We couldn\'t log you in with those details/i')
    ).toBeVisible()

    // Should remain on login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('toggles password visibility', async ({ page }) => {
    await page.goto('/login')

    // Enter password
    const passwordInput = page.locator('input[type="password"]#password')
    await passwordInput.fill('TestPassword123')

    // Password should be masked by default
    await expect(passwordInput).toHaveAttribute('type', 'password')

    // Click show password
    await page.click('text=/Show password/i')

    // Password should now be visible
    const passwordInputVisible = page.locator('input[type="text"]#password')
    await expect(passwordInputVisible).toHaveAttribute('type', 'text')
    await expect(passwordInputVisible).toHaveValue('TestPassword123')

    // Click hide password
    await page.click('text=/Hide password/i')

    // Password should be masked again
    await expect(passwordInput).toHaveAttribute('type', 'password')
  })

  test('clears validation errors when user starts typing', async ({ page }) => {
    await page.goto('/login')

    // Trigger validation errors
    await page.click('button:has-text("Continue")')
    await expect(page.locator('text=/Error: Enter your username/i')).toBeVisible()

    // Start typing in username field
    await page.fill('input[type="text"]#username', 'a')

    // Username error should disappear
    await expect(page.locator('text=/Error: Enter your username/i')).not.toBeVisible()

    // Password error should still be visible
    await expect(page.locator('text=/Error: Enter your password/i')).toBeVisible()
  })

  test('stores username in localStorage after successful sign-in', async ({ page }) => {
    await page.goto('/login')

    // Enter valid credentials
    await page.fill('input[type="text"]#username', 'sasha.patel@gmail.com')
    await page.fill('input[type="password"]#password', 'Demo1234!')

    // Click continue
    await page.click('button:has-text("Continue")')

    // Wait for navigation to proof page
    await page.waitForURL(/\/proof/)

    // Check that username was stored
    const lastUsername = await page.evaluate(() => localStorage.getItem('last_username'))
    expect(lastUsername).toBe('sasha.patel@gmail.com')
  })
})
