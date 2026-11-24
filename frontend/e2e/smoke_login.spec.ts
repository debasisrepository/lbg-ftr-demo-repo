import { test, expect } from './_pipeline_guard'

test.describe('Smoke Login E2E', () => {
  test('logs in with seed credentials and sees landing page', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login')

    // Verify login form is present
    await expect(page.getByText('Receivables & Collections')).toBeVisible()
    
    // Fill in login form with seed analyst credentials (from backend seed)
    const usernameInput = page.getByLabel(/username/i)
    const passwordInput = page.getByLabel(/password/i)
    const submitButton = page.getByRole('button', { name: /sign in/i })
    
    await expect(usernameInput).toBeVisible()
    await expect(passwordInput).toBeVisible()
    await expect(submitButton).toBeVisible()
    
    await usernameInput.fill('analyst1')
    await passwordInput.fill('analyst123')

    // Submit form
    await submitButton.click()

    // Wait for successful navigation away from login page
    await page.waitForURL((url) => !url.pathname.includes('/login'), { timeout: 10000 })
    
    // Verify we're on the landing page
    await expect(page).toHaveURL('/')
    
    // Verify authenticated state - landing page greeting is visible
    await expect(page.getByText(/Good morning/i)).toBeVisible({ timeout: 5000 })
  })
})
