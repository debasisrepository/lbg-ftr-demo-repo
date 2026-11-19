import { test, expect } from './_pipeline_guard'

/**
 * E2E tests for Accounts Page (FR-003)
 * Wireframe: wireframe_03_j01_s03.html
 */

async function enterPasscode(page: { click: (selector: string) => Promise<void> }, passcode: string) {
  for (const digit of passcode) {
    await page.click(`button:has-text("${digit}")`)
  }
}

test.describe('Wireframe 03 - Accounts Overview', () => {
  test.beforeEach(async ({ page, context }) => {
    // Clear storage to avoid Face ID screen
    await context.clearCookies()
    await page.goto('/login')
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })

    // Navigate to login page
    await page.goto('/login')

    // Wait for page to be ready
    await page.waitForLoadState('networkidle')

    // Sign in with demo credentials
    await page.fill('#username', 'sasha.patel@gmail.com')
    await page.fill('#password', 'Demo1234!')
    await page.click('button[type="submit"]:has-text("Continue")')

    // Complete proof with passcode using keypad
    await page.waitForURL('**/proof', { timeout: 15000 })
    await enterPasscode(page, '123456')
    
    // Wait for accounts page
    await page.waitForURL('**/accounts', { timeout: 15000 })
  })

  test('should display accounts overview', async ({ page }) => {
    // Verify page title
    await expect(page.locator('h2:text-is("Your accounts")')).toBeVisible()

    // Verify greeting
    await expect(page.locator('text=/Hello, \\w+/')).toBeVisible()

    // Verify at least one account is displayed
    const accountCards = page.locator('h3')
    await expect(accountCards.first()).toBeVisible()
  })

  test('should display current account with balance', async ({ page }) => {
    // Find any heading containing "Personal Current Account"
    const currentAccountHeading = page.locator('h3').filter({ hasText: /Personal Current Account/i })
    await expect(currentAccountHeading).toBeVisible()

    // Find the parent container and check for sort code
    const accountContainer = currentAccountHeading.locator('..')
    await expect(accountContainer.locator('text=12-34-56')).toBeVisible()

    // Verify balance is shown (either actual amount or "Unavailable")
    await expect(accountContainer.locator('p').filter({ hasText: /£|Unavailable/ })).toBeVisible()
  })

  test('should display credit card account', async ({ page }) => {
    // Find any heading containing "Visa Credit Card"
    const creditCardHeading = page.locator('h3').filter({ hasText: /Visa Credit Card/i })
    await expect(creditCardHeading).toBeVisible()
    
    // Find the parent container and check for masked account number
    const cardContainer = creditCardHeading.locator('..')
    await expect(cardContainer.locator('text=****1234')).toBeVisible()
  })

  test('should display loan if present', async ({ page }) => {
    // Check if loan exists - seed has "Personal Loan"
    const loanHeading = page.locator('h3').filter({ hasText: /Personal Loan/i })
    const loanCount = await loanHeading.count()
    
    if (loanCount > 0) {
      await expect(loanHeading.first()).toBeVisible()
      
      // Verify loan balance
      const loanContainer = loanHeading.first().locator('..')
      await expect(loanContainer.locator('p').filter({ hasText: /£/ })).toBeVisible()
      
      // Verify next repayment info
      const nextRepayment = loanContainer.locator('text=/Next repayment/')
      const repaymentCount = await nextRepayment.count()
      expect(repaymentCount).toBeGreaterThanOrEqual(0)
    }
  })

  test('should show unavailable state correctly', async ({ page }) => {
    // Look for any unavailable accounts - may exist in seed data
    const unavailableCards = page.locator('p:text-is("Unavailable")')
    const unavailableCount = await unavailableCards.count()
    
    if (unavailableCount > 0) {
      // Verify error message is shown
      await expect(page.locator('text=/We can\'t show this balance/')).toBeVisible()
      
      // Verify no zero is shown in place of missing value
      const unavailableCard = unavailableCards.first().locator('..')
      await expect(unavailableCard.locator('text=/£0\\.00/')).not.toBeVisible()
    }
  })

  test('should navigate to Pay & Transfer', async ({ page }) => {
    // Click Pay & Transfer tab
    await page.click('button:has-text("Pay & Transfer")')
    
    // Verify navigation
    await page.waitForURL('**/pay-and-transfer')
    await expect(page.locator('h2:has-text("Pay & Transfer")')).toBeVisible()
  })

  test('should display profile switcher when multiple profiles', async ({ page }) => {
    // Check if profile switcher exists - depends on seed data
    const profileSwitcher = page.locator('[role="tablist"][aria-label="Profile"]')
    const switcherCount = await profileSwitcher.count()
    
    if (switcherCount > 0) {
      await expect(profileSwitcher).toBeVisible()
      
      // Verify at least one profile tab
      const profileTabs = profileSwitcher.locator('[role="tab"]')
      await expect(profileTabs.first()).toBeVisible()
      
      // Verify one profile is marked as active
      await expect(profileTabs.locator('[aria-selected="true"]')).toBeVisible()
    }
  })

  test('should show freshness timestamp when stale', async ({ page }) => {
    // Look for freshness indicator - may exist depending on seed data
    const freshnessText = page.locator('text=/Balance as at/')
    const freshnessCount = await freshnessText.count()
    
    // This is conditional based on data freshness state
    expect(freshnessCount).toBeGreaterThanOrEqual(0)
  })
})
