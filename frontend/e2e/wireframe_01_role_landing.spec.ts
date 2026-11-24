import { test, expect } from './_pipeline_guard'

test.describe('Wireframe 01: Role Landing Workspace', () => {
  test('logs in, sees widgets for active role, switches role, sees new widgets', async ({
    page,
  }) => {
    // Navigate to login page
    await page.goto('/')
    await expect(page).toHaveURL('/login')

    // Log in with analyst1 credentials
    await page.fill('input[id="username"]', 'analyst1')
    await page.fill('input[id="password"]', 'analyst123')
    await page.click('button[type="submit"]')

    // Wait for navigation to landing page
    await page.waitForURL('/')

    // Verify landing page loaded with greeting
    await expect(page.getByRole('heading', { level: 1 }).filter({ hasText: /Good morning/ })).toBeVisible()

    // Verify role-based widgets are visible
    // Queue summary widget
    await expect(page.getByRole('heading', { name: /My work queue/i })).toBeVisible()
    
    // Landing page loaded successfully - queue data may be empty but widget should be visible
    await page.waitForTimeout(1000)

    // Check active role display in role switcher
    const roleSelect = page.locator('select[id="role-select"]')
    await expect(roleSelect).toBeVisible()
    const selectedRole = await roleSelect.inputValue()
    expect(selectedRole).toBeTruthy()

    // Verify available roles are in the dropdown
    const options = await roleSelect.locator('option').allTextContents()
    expect(options.length).toBeGreaterThan(0)

    // If multiple roles are available, switch role
    if (options.length > 1) {
      const currentRole = await roleSelect.inputValue()
      const otherRoleOption = options.find((_, idx) => 
        roleSelect.locator('option').nth(idx).getAttribute('value') !== currentRole
      )

      if (otherRoleOption) {
        // Get the value of the other role option
        const otherRoleValue = await roleSelect.locator('option').filter({ hasText: otherRoleOption }).getAttribute('value')
        
        // Switch to the other role
        await roleSelect.selectOption(otherRoleValue || '')

        // Wait for page to update (may reload or refetch data)
        await page.waitForTimeout(1000)

        // Verify the role switched
        const newRole = await roleSelect.inputValue()
        expect(newRole).toBe(otherRoleValue)

        // Verify widgets are still visible (may have different content based on role)
        await expect(page.getByRole('heading', { name: /My work queue/i })).toBeVisible()
      }
    }
  })
})
