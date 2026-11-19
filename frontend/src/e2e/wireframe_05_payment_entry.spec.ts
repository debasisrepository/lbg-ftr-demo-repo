/**
 * E2E Test: Wireframe 05 - Payment Entry and Approval
 * Tests FR-005: Enter payment details, approve with SCA
 */

import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 05: Payment Entry and Approval', () => {
  test.beforeEach(async ({ page }) => {
    // Clear storage and navigate to login
    await page.context().clearCookies()
    await page.goto('/login')
    try {
      await page.evaluate(() => {
        localStorage.clear()
        sessionStorage.clear()
      })
    } catch (e) {
      // Ignore SecurityError
    }

    // Navigate to login page and wait for it to load
    await page.goto('/login')
    await page.waitForLoadState('networkidle')

    // Sign in
    await page.fill('#username', 'sasha.patel@gmail.com')
    await page.fill('#password', 'Demo1234!')
    await page.click('button[type="submit"]')

    // Wait for proof page
    await page.waitForURL('**/proof', { timeout: 10000 })

    // Enter passcode using numeric keypad
    const passcode = '123456'
    for (const digit of passcode) {
      await page.click(`button:has-text("${digit}")`)
    }

    // Wait for accounts page
    await page.waitForURL('**/accounts', { timeout: 10000 })
  })

  test('displays payment entry form with payee details', async ({ page }) => {
    // Navigate to Pay & Transfer
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')

    // Select a payee (Jamie Clarke from seed data)
    await page.click('text=Jamie Clarke')

    // Wait for payment entry page
    await page.waitForURL('**/pay')

    // Verify page elements
    await expect(page.locator('h2')).toContainText('Pay Jamie Clarke')
    await expect(page.locator('text=12-34-56')).toBeVisible()

    // Verify form fields
    await expect(page.getByText('From', { exact: true })).toBeVisible()
    await expect(page.getByText('Amount')).toBeVisible()
    await expect(page.getByText('Reference')).toBeVisible()
  })

  test('validates amount exceeding balance', async ({ page }) => {
    // Navigate to Pay & Transfer
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')

    // Select payee
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    // Enter amount exceeding balance
    const amountInput = page.locator('input[id="amount"]')
    await amountInput.fill('5000.00')

    // Try to pay
    await page.click('button:has-text("Pay £5000.00")')

    // Wait for error message
    await expect(page.locator('text=/You can pay up to/i')).toBeVisible({ timeout: 10000 })
  })

  test('allows valid payment entry and proceeds to review', async ({ page }) => {
    // Navigate to Pay & Transfer
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')

    // Select payee
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    // Enter valid payment details
    const amountInput = page.locator('input[id="amount"]')
    await amountInput.fill('40.00')

    const refInput = page.locator('input[id="reference"]')
    await refInput.fill('Test payment')

    // Click pay button
    await page.getByRole('button', { name: 'Pay £40.00' }).click()

    // Wait for review page
    await page.waitForURL('**/payment/review', { timeout: 10000 })

    // Verify review page loaded
    await expect(page.locator('h2:has-text("Approve payment")')).toBeVisible()
  })

  test('displays payment review with dynamic linking details', async ({ page }) => {
    // Navigate through payment entry
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.fill('input[id="reference"]', 'Test')
    await page.click('button:has-text("Pay £40.00")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })

    // Verify payment details in review
    await expect(page.locator('text=Current Account').first()).toBeVisible()
    await expect(page.locator('text=Jamie Clarke').first()).toBeVisible()
    await expect(page.locator('text=£40.00').first()).toBeVisible()
    await expect(page.locator('text=Test').first()).toBeVisible()
  })

  test('shows Face ID approval option', async ({ page }) => {
    // Navigate through payment entry
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay £40.00")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })

    // Verify Face ID panel
    await expect(page.locator('text=/Approve.*with Face ID/i').first()).toBeVisible()
    await expect(page.getByRole('button', { name: /Approve with Face ID/i }).first()).toBeVisible()
  })

  test('allows cancellation from review screen', async ({ page }) => {
    // Navigate through payment entry
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay £40.00")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })

    // Click cancel
    await page.click('button:has-text("Cancel")')

    // Should return to accounts
    await page.waitForURL('**/accounts', { timeout: 10000 })
  })

  test('completes payment approval and shows outcome', async ({ page }) => {
    // Navigate through payment entry
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    await page.fill('input[id="amount"]', '40.00')
    await page.click('button:has-text("Pay £40.00")')

    await page.waitForURL('**/payment/review', { timeout: 10000 })

    // Approve payment
    await page.click('button:has-text("Approve with Face ID")')

    // Wait for outcome page
    await page.waitForURL('**/payment/outcome', { timeout: 10000 })

    // Verify outcome page elements
    await expect(
      page.locator('h2').filter({ hasText: /Payment sent|Payment pending/i })
    ).toBeVisible({ timeout: 10000 })
  })

  test('navigates back from entry page', async ({ page }) => {
    // Navigate to payment entry
    await page.click('text=Pay & Transfer')
    await page.waitForURL('**/pay-and-transfer')
    await page.click('text=Jamie Clarke')
    await page.waitForURL('**/pay')

    // Click back button
    await page.click('button[aria-label="Back"]')

    // Should return to pay & transfer
    await page.waitForURL('**/pay-and-transfer', { timeout: 10000 })
  })
})
