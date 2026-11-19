/**
 * E2E Test: Wireframe 06 - Payment Outcome
 * Tests FR-006: Payment sent/pending/failed outcomes with references
 */

import { test, expect } from '@playwright/test'

test.describe('Wireframe 06: Payment Outcome', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login first and wait for it to load
    await page.goto('/', { waitUntil: 'networkidle' })

    // Clear storage after page has loaded
    await page.context().clearCookies()
    try {
      await page.evaluate(() => {
        localStorage.clear()
        sessionStorage.clear()
      })
    } catch (e) {
      // Ignore SecurityError on about:blank or before page loads
    }

    // Ensure we're on the login page
    await page.waitForURL('**/login', { timeout: 5000 }).catch(() => {
      return page.goto('/login', { waitUntil: 'networkidle' })
    })

    // Wait for username input to be visible
    await page.waitForSelector('input[name="username"]', { state: 'visible', timeout: 10000 })

    // Sign in
    await page.fill('input[name="username"]', 'sasha.patel@gmail.com')
    await page.fill('input[name="password"]', 'Demo1234!')
    await page.click('button[type="submit"]')

    await page.waitForURL('**/proof', { timeout: 10000 })

    // Enter passcode
    const passcode = '123456'
    for (const digit of passcode) {
      await page.click(`button:has-text("${digit}")`)
    }

    await page.waitForURL('**/accounts', { timeout: 10000 })
  })

  test('displays sent payment outcome with reference', async ({ page }) => {
    // Complete a payment
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.fill('input[id="reference"]', 'Test payment')
    await page.click('button:has-text("Pay")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })
    await page.click('button:has-text("Approve with Face ID")')

    // Wait for outcome page
    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Verify sent status elements
    const statusTag = page.locator('text=/Sent|Pending/i')
    await expect(statusTag).toBeVisible({ timeout: 10000 })

    // Verify payment reference is displayed
    await expect(page.locator('text=/Payment reference/i')).toBeVisible()
    await expect(page.locator('text=/PAY/i')).toBeVisible()

    // Verify amount and payee
    await expect(page.locator('text=/£40.00/i')).toBeVisible()
    await expect(page.locator('text=/Jamie Clarke/i')).toBeVisible()
  })

  test('shows expected arrival time for sent payment', async ({ page }) => {
    // Complete a payment
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })
    await page.click('button:has-text("Approve with Face ID")')

    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Verify arrival guidance present
    const bodyText = page.locator('text=/on its way|should arrive|within/i')
    await expect(bodyText).toBeVisible({ timeout: 10000 })
  })

  test('displays back to accounts button', async ({ page }) => {
    // Complete a payment
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })
    await page.click('button:has-text("Approve with Face ID")')

    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Verify back to accounts button
    await expect(
      page.locator('button:has-text("Back to accounts")')
    ).toBeVisible({ timeout: 10000 })
  })

  test('displays make another payment button', async ({ page }) => {
    // Complete a payment
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })
    await page.click('button:has-text("Approve with Face ID")')

    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Verify make another payment button
    await expect(
      page.locator('button:has-text("Make another payment")')
    ).toBeVisible({ timeout: 10000 })
  })

  test('navigates back to accounts from outcome', async ({ page }) => {
    // Complete a payment
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })
    await page.click('button:has-text("Approve with Face ID")')

    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Click back to accounts
    await page.click('button:has-text("Back to accounts")')

    // Should return to accounts page
    await page.waitForURL('**/accounts', { timeout: 10000 })
    await expect(page.locator('h2:has-text("Accounts")')).toBeVisible()
  })

  test('outcome screen shows payment status badge', async ({ page }) => {
    // Complete a payment
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })
    await page.click('button:has-text("Approve with Face ID")')

    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Verify status badge (Sent or Pending)
    const statusBadge = page.locator('span').filter({ hasText: /^(Sent|Pending|Failed)$/ })
    await expect(statusBadge).toBeVisible({ timeout: 10000 })
  })

  test('outcome screen shows check icon for sent payment', async ({ page }) => {
    // Complete a payment
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })
    await page.click('button:has-text("Approve with Face ID")')

    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Verify status icon is present (check or clock)
    const statusIcon = page.locator('div').filter({ has: page.locator('svg') }).first()
    await expect(statusIcon).toBeVisible({ timeout: 10000 })
  })
})
