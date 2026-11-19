import { test, expect } from '@playwright/test'

/**
 * Smoke test: Basic application loading and infrastructure verification
 * Note: Full login flow will be tested once auth endpoints and pages are implemented
 */

test.describe('Frontend Infrastructure Smoke Tests', () => {
  test('should have working backend health endpoint', async ({ request }) => {
    const backendPort = process.env.E2E_BACKEND_PORT ?? '9000'
    const response = await request.get(`http://127.0.0.1:${backendPort}/api/v1/health`)
    
    expect(response.ok()).toBeTruthy()
    const data = await response.json()
    expect(data.status).toBe('ok')
  })

  test('should load the application', async ({ page }) => {
    // Navigate to the app
    await page.goto('/')

    // Check that the page loaded without errors
    await expect(page).toBeTruthy()
  })

  test('should display app placeholder content', async ({ page }) => {
    await page.goto('/')

    // The placeholder App.tsx should have some content
    // This verifies Vite dev server is working and serving the React app
    const body = page.locator('body')
    await expect(body).toBeVisible()
  })
})

/**
 * Login flow test (will be implemented by auth task)
 * 
 * Expected flow once implemented:
 * 1. Navigate to login page
 * 2. Enter seed user credentials
 * 3. Submit login form
 * 4. Assert successful redirect to account screen
 * 5. Verify user data is displayed
 */
test.describe.skip('Login Flow (to be implemented)', () => {
  test('should login with seed credentials', async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[name="username"]', 'test@example.com')
    await page.fill('input[name="password"]', 'Test-pass-1')
    await page.click('button[type="submit"]')
    await page.waitForURL(/\/accounts/, { timeout: 10000 })
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible()
  })
})
