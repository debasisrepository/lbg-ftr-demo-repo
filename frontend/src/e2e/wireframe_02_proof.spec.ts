/**
 * E2E test for wireframe_02: Proof (FR-002)
 * Tests the complete passcode proof flow
 */

import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 02: Proof', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and sign in first
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })

    // Sign in to reach proof screen
    await page.goto('/login')
    await page.fill('input[type="text"]#username', 'sasha.patel@gmail.com')
    await page.fill('input[type="password"]#password', 'Demo1234!')
    await page.click('button:has-text("Continue")')

    // Wait for proof page
    await page.waitForURL(/\/proof/)
    await expect(page.locator('h2:has-text("Enter your passcode")')).toBeVisible()
  })

  test('enters valid passcode and navigates to accounts screen', async ({ page }) => {
    // Enter passcode: 123456 (from seed data)
    const keypad = page.locator('[aria-label="Numeric keypad"]')
    await keypad.locator('button:has-text("1")').first().click()
    await keypad.locator('button:has-text("2")').first().click()
    await keypad.locator('button:has-text("3")').first().click()
    await keypad.locator('button:has-text("4")').first().click()
    await keypad.locator('button:has-text("5")').first().click()
    await keypad.locator('button:has-text("6")').first().click()

    // Should navigate to accounts page
    await page.waitForURL(/\/accounts/, { timeout: 10000 })
    
    // Should see accounts page content
    await expect(page.locator('h2:has-text("Your accounts")')).toBeVisible()
  })

  test('shows passcode entry progress', async ({ page }) => {
    // Initially 0 digits entered
    await expect(page.locator('[aria-label*="0 of 6 digits entered"]')).toBeVisible()

    // Enter 1 digit
    const keypad = page.locator('[aria-label="Numeric keypad"]')
    await keypad.locator('button:has-text("1")').first().click()

    // Should show 1 digit entered
    await expect(page.locator('[aria-label*="1 of 6 digits entered"]')).toBeVisible()

    // Enter 4 more digits
    await keypad.locator('button:has-text("2")').first().click()
    await keypad.locator('button:has-text("3")').first().click()
    await keypad.locator('button:has-text("4")').first().click()
    await keypad.locator('button:has-text("5")').first().click()

    // Should show 5 digits entered
    await expect(page.locator('[aria-label*="5 of 6 digits entered"]')).toBeVisible()
  })

  test('deletes entered digits', async ({ page }) => {
    const keypad = page.locator('[aria-label="Numeric keypad"]')
    
    // Enter 3 digits
    await keypad.locator('button:has-text("1")').first().click()
    await keypad.locator('button:has-text("2")').first().click()
    await keypad.locator('button:has-text("3")').first().click()

    await expect(page.locator('[aria-label*="3 of 6 digits entered"]')).toBeVisible()

    // Click delete
    await keypad.locator('button[aria-label="Delete"]').click()

    // Should show 2 digits entered
    await expect(page.locator('[aria-label*="2 of 6 digits entered"]')).toBeVisible()

    // Click delete again
    await keypad.locator('button[aria-label="Delete"]').click()

    // Should show 1 digit entered
    await expect(page.locator('[aria-label*="1 of 6 digits entered"]')).toBeVisible()
  })

  test('toggles passcode visibility', async ({ page }) => {
    const keypad = page.locator('[aria-label="Numeric keypad"]')
    
    // Enter 2 digits
    await keypad.locator('button:has-text("1")').first().click()
    await keypad.locator('button:has-text("2")').first().click()

    // By default, passcode should be masked (shown as bullets)
    // Click show passcode
    await page.click('text=/Show passcode/i')

    // Should now show "Hide passcode" link
    await expect(page.locator('text=/Hide passcode/i')).toBeVisible()

    // Click hide passcode
    await page.click('text=/Hide passcode/i')

    // Should show "Show passcode" again
    await expect(page.locator('text=/Show passcode/i')).toBeVisible()
  })

  test('shows error for wrong passcode with attempts remaining', async ({ page }) => {
    const keypad = page.locator('[aria-label="Numeric keypad"]')
    
    // Enter wrong passcode: 000000
    for (let i = 0; i < 6; i++) {
      await keypad.locator('button:has-text("0")').click()
    }

    // Should show error message with attempts remaining
    await expect(
      page.locator('text=/That passcode isn\'t right.*attempts left/i')
    ).toBeVisible({ timeout: 10000 })

    // Boxes should be cleared
    await expect(page.locator('[aria-label*="0 of 6 digits entered"]')).toBeVisible()
  })

  test('JWT token is stored after successful proof', async ({ page }) => {
    const keypad = page.locator('[aria-label="Numeric keypad"]')
    
    // Enter correct passcode: 123456
    await keypad.locator('button:has-text("1")').first().click()
    await keypad.locator('button:has-text("2")').first().click()
    await keypad.locator('button:has-text("3")').first().click()
    await keypad.locator('button:has-text("4")').first().click()
    await keypad.locator('button:has-text("5")').first().click()
    await keypad.locator('button:has-text("6")').first().click()

    // Wait for navigation
    await page.waitForURL(/\/accounts/, { timeout: 10000 })

    // Check that JWT token was stored
    const token = await page.evaluate(() => localStorage.getItem('lbg_ftr_demo_auth_token'))
    expect(token).toBeTruthy()
    expect(typeof token).toBe('string')
  })

  test('session storage is cleared after successful proof', async ({ page }) => {
    // Session storage should have pending data before proof
    const sessionIdBefore = await page.evaluate(() => 
      sessionStorage.getItem('pending_session_id')
    )
    expect(sessionIdBefore).toBeTruthy()

    const keypad = page.locator('[aria-label="Numeric keypad"]')
    
    // Enter correct passcode: 123456
    await keypad.locator('button:has-text("1")').first().click()
    await keypad.locator('button:has-text("2")').first().click()
    await keypad.locator('button:has-text("3")').first().click()
    await keypad.locator('button:has-text("4")').first().click()
    await keypad.locator('button:has-text("5")').first().click()
    await keypad.locator('button:has-text("6")').first().click()

    // Wait for navigation
    await page.waitForURL(/\/accounts/, { timeout: 10000 })

    // Session storage should be cleared
    const sessionIdAfter = await page.evaluate(() => 
      sessionStorage.getItem('pending_session_id')
    )
    expect(sessionIdAfter).toBeNull()

    const customerIdAfter = await page.evaluate(() => 
      sessionStorage.getItem('pending_customer_id')
    )
    expect(customerIdAfter).toBeNull()
  })

  test('navigates back to login from proof page', async ({ page }) => {
    // Click back button
    await page.click('button[aria-label="Back"]')

    // Should navigate to previous page (login)
    await expect(page).toHaveURL(/\/login/)
  })

  test('shows Face ID option link', async ({ page }) => {
    // Should show Face ID option (even if not functional in web)
    await expect(page.locator('text=/Use Face ID instead/i')).toBeVisible()
  })
})
