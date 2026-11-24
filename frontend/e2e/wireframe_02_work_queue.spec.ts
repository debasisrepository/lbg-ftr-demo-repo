import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 02: Work Queue', () => {
  test('logs in, navigates to queue, filters, clicks refresh, waits for completion, sees updated ranks', async ({
    page,
  }) => {
    // Log in
    await page.goto('/')
    await expect(page).toHaveURL('/login')

    await page.fill('input[id="username"]', 'analyst1')
    await page.fill('input[id="password"]', 'analyst123')
    await page.click('button[type="submit"]')

    // Wait for landing page
    await page.waitForURL('/')

    // Navigate to work queue
    await page.click('a[href="/queue"]')
    await page.waitForURL('/queue')

    // Verify queue page loaded
    await expect(page.getByRole('heading', { name: 'Work queue', level: 1 })).toBeVisible()

    // Verify tabs are present
    await expect(page.getByRole('tab', { name: /Ready for action/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Promise on file/i })).toBeVisible()
    await expect(page.getByRole('tab', { name: /Non-standard/i })).toBeVisible()

    // Verify filter controls are present
    await expect(page.getByLabel(/Show/i)).toBeVisible()
    await expect(page.getByLabel(/Customer/i)).toBeVisible()

    // Apply a filter (show only standard items)
    await page.selectOption('select[id="flag-filter"]', 'standard')
    await page.waitForTimeout(500)

    // Check if table is present (may be empty depending on seed data)
    const table = page.locator('table')
    const emptyMessage = page.getByText(/No items in this queue/i)
    await expect(table.or(emptyMessage).first()).toBeVisible()

    // Click refresh button
    const refreshButton = page.getByRole('button', { name: /Refresh queue/i })
    await expect(refreshButton).toBeVisible()
    await refreshButton.click()

    // Wait for refresh to start - look for "Refreshing..." button specifically
    await expect(page.getByRole('button', { name: /Refreshing/i })).toBeVisible({ timeout: 10000 })

    // Wait for refresh to complete - button should return to "Refresh queue" state
    await expect(page.getByRole('button', { name: /Refresh queue/i })).toBeVisible({ timeout: 40000 })

    // Verify queue data is displayed (ranks should be visible if items exist)
    const hasItems = await page.locator('table tbody tr').count()
    if (hasItems > 0) {
      // Verify rank column exists
      await expect(page.getByRole('columnheader', { name: /Rank/i })).toBeVisible()
      
      // Verify at least one rank is displayed
      const firstRank = page.locator('table tbody tr:first-child td:first-child')
      await expect(firstRank).toBeVisible()
    }
  })

  test('switches between queue state tabs', async ({ page }) => {
    // Log in
    await page.goto('/')
    await expect(page).toHaveURL('/login')

    await page.fill('input[id="username"]', 'analyst1')
    await page.fill('input[id="password"]', 'analyst123')
    await page.click('button[type="submit"]')

    await page.waitForURL('/')

    // Navigate to queue
    await page.click('a[href="/queue"]')
    await page.waitForURL('/queue')

    // Click on "Promise on file" tab
    const promiseTab = page.getByRole('tab', { name: /Promise on file/i })
    await promiseTab.click()

    // Verify tab is active
    await expect(promiseTab).toHaveAttribute('aria-selected', 'true')

    // Click on "Non-standard" tab
    const nonStandardTab = page.getByRole('tab', { name: /Non-standard/i })
    await nonStandardTab.click()

    // Verify tab is active
    await expect(nonStandardTab).toHaveAttribute('aria-selected', 'true')
  })
})
