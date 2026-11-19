# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: wireframe_05_j01_s05.spec.ts >> Wireframe 05 - Payment Entry and Approval (FR-005) >> should show approval modal with dynamic linking
- Location: e2e/wireframe_05_j01_s05.spec.ts:82:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('[role="dialog"]')
Expected: visible
Error: strict mode violation: locator('[role="dialog"]') resolved to 2 elements:
    1) <div role="dialog" tabindex="-1" aria-modal="true" class="cds--modal-container" aria-label="Check this payment carefully">…</div> aka getByLabel('Check this payment carefully')
    2) <div role="dialog" tabindex="-1" aria-modal="true" class="cds--modal-container" aria-label="Approve with Face ID">…</div> aka getByLabel('Approve with Face ID')

Call log:
  - Expect "toBeVisible" locator('[role="dialog"]') with timeout 5000ms
  - waiting for locator('[role="dialog"]')

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - banner [ref=e5]:
    - button "Back to payees" [ref=e6] [cursor=pointer]
    - generic [ref=e9]: Your Bank
  - main [ref=e10]:
    - heading "Make a payment" [level=1] [ref=e11]
    - generic "Paying Jamie Clarke" [ref=e12]:
      - generic [ref=e13]:
        - paragraph [ref=e14]: Jamie Clarke
        - paragraph [ref=e15]: 04-00-04 · ****3746
    - generic [ref=e19]:
      - generic [ref=e20]:
        - generic [ref=e21]: From
        - textbox "From" [ref=e22]: Admin Current Account · 12-34-56 | ****1234
        - paragraph [ref=e23]: Available balance £1,248.36
      - generic [ref=e24]:
        - generic [ref=e25]: Amount
        - generic [ref=e26]:
          - generic [aria-hidden]: £
          - textbox "Amount" [ref=e27]: "50.00"
        - paragraph [ref=e28]: Payments are in pounds sterling (GBP).
      - generic [ref=e29]:
        - generic [ref=e30]: Reference (optional)
        - textbox "Reference (optional)" [ref=e31]: Test payment
        - paragraph [ref=e32]: Up to 18 characters.
      - status [ref=e33]:
        - generic [ref=e34]:
          - img "info icon" [ref=e35]
          - generic [ref=e38]:
            - generic [ref=e39]: You'll approve with Face ID
            - generic [ref=e40]: Your approval is tied to Jamie Clarke and £50.00. If you change either, you'll need to approve again.
      - button "Pay £50.00" [disabled] [ref=e41]
```

# Test source

```ts
  1   | import { test, expect } from './_pipeline_guard';
  2   | 
  3   | test.describe('Wireframe 05 - Payment Entry and Approval (FR-005)', () => {
  4   |   test.beforeEach(async ({ page }) => {
  5   |     // Navigate to login
  6   |     await page.goto('/');
  7   |     
  8   |     // Login with seed credentials
  9   |     await page.fill('#username', 'admin@example.com');
  10  |     await page.fill('#password', 'admin123');
  11  |     await page.click('button[type="submit"]');
  12  |     
  13  |     // Complete step-up with passcode
  14  |     await page.waitForURL('**/step-up');
  15  |     const passcodeInputs = page.locator('input[aria-label*="Passcode digit"]');
  16  |     await passcodeInputs.nth(0).fill('1');
  17  |     await passcodeInputs.nth(1).fill('2');
  18  |     await passcodeInputs.nth(2).fill('3');
  19  |     await passcodeInputs.nth(3).fill('4');
  20  |     await passcodeInputs.nth(4).fill('5');
  21  |     await passcodeInputs.nth(5).fill('6');
  22  |     await passcodeInputs.nth(5).press('Enter');
  23  |     
  24  |     // Wait for accounts page
  25  |     await page.waitForURL('**/accounts');
  26  |     
  27  |     // Navigate to payees page
  28  |     await page.click('button:has-text("Pay & Transfer")');
  29  |     await page.waitForURL('**/payees');
  30  |   });
  31  | 
  32  |   test('should display payment entry form with payee and account details', async ({ page }) => {
  33  |     // Select a payee
  34  |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  35  |     
  36  |     // Continue to payment entry
  37  |     await page.click('button:has-text("Continue to payment")');
  38  |     await page.waitForURL('**/payment/entry');
  39  |     
  40  |     // Verify payment entry page loads
  41  |     await expect(page.locator('h1')).toHaveText('Make a payment');
  42  |     // Target the payee panel specifically, not the notification that also mentions the payee
  43  |     await expect(page.locator('[aria-label*="Paying"] p').filter({ hasText: 'Jamie Clarke' })).toBeVisible();
  44  |     await expect(page.locator('text=04-00-04')).toBeVisible();
  45  |     
  46  |     // Verify from account is readonly
  47  |     const fromInput = page.locator('#from');
  48  |     await expect(fromInput).toHaveAttribute('readonly');
  49  |     await expect(fromInput).toHaveValue(/Current Account/);
  50  |     
  51  |     // Verify amount field
  52  |     const amountInput = page.locator('#amount');
  53  |     await expect(amountInput).toBeVisible();
  54  |     await expect(amountInput).toHaveValue('250.00');
  55  |     
  56  |     // Verify reference field
  57  |     const referenceInput = page.locator('#reference');
  58  |     await expect(referenceInput).toBeVisible();
  59  |   });
  60  | 
  61  |   test('should show inline error when amount exceeds balance', async ({ page }) => {
  62  |     // Select a payee and navigate to payment entry
  63  |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  64  |     await page.click('button:has-text("Continue to payment")');
  65  |     await page.waitForURL('**/payment/entry');
  66  |     
  67  |     // Enter amount exceeding balance
  68  |     const amountInput = page.locator('#amount');
  69  |     await amountInput.clear();
  70  |     await amountInput.fill('1500.00');
  71  |     
  72  |     // Click pay button
  73  |     await page.click('button:has-text("Pay £1,500.00")');
  74  |     
  75  |     // Wait for error message
  76  |     await expect(page.locator('text=/Payment amount exceeds/i')).toBeVisible();
  77  |     
  78  |     // Verify pay button is still enabled but error shown
  79  |     await expect(page.locator('button:has-text("Pay £1,500.00")')).toBeVisible();
  80  |   });
  81  | 
  82  |   test('should show approval modal with dynamic linking', async ({ page }) => {
  83  |     // Select a payee and navigate to payment entry
  84  |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  85  |     await page.click('button:has-text("Continue to payment")');
  86  |     await page.waitForURL('**/payment/entry');
  87  |     
  88  |     // Enter valid payment details
  89  |     const amountInput = page.locator('#amount');
  90  |     await amountInput.clear();
  91  |     await amountInput.fill('50.00');
  92  |     
  93  |     const referenceInput = page.locator('#reference');
  94  |     await referenceInput.fill('Test payment');
  95  |     
  96  |     // Click pay button
  97  |     await page.click('button:has-text("Pay £50.00")');
  98  |     
  99  |     // Wait for approval modal (target the modal specifically)
> 100 |     await expect(page.locator('[role="dialog"]')).toBeVisible();
      |                                                   ^ Error: expect(locator).toBeVisible() failed
  101 |     await expect(page.locator('[role="dialog"]').locator('h2:has-text("Approve with Face ID")')).toBeVisible();
  102 |     
  103 |     // Verify dynamic link summary shows payee and amount
  104 |     await expect(page.locator('text=Jamie Clarke')).toBeVisible();
  105 |     await expect(page.locator('text=£50.00')).toBeVisible();
  106 |     
  107 |     // Verify cancel and approve buttons present
  108 |     await expect(page.locator('button:has-text("Cancel")')).toBeVisible();
  109 |     await expect(page.locator('button:has-text("Approve")')).toBeVisible();
  110 |   });
  111 | 
  112 |   test('should navigate to outcome page after successful approval', async ({ page }) => {
  113 |     // Select a payee and navigate to payment entry
  114 |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  115 |     await page.click('button:has-text("Continue to payment")');
  116 |     await page.waitForURL('**/payment/entry');
  117 |     
  118 |     // Enter valid payment details
  119 |     const amountInput = page.locator('#amount');
  120 |     await amountInput.clear();
  121 |     await amountInput.fill('50.00');
  122 |     
  123 |     // Click pay button
  124 |     await page.click('button:has-text("Pay £50.00")');
  125 |     
  126 |     // Wait for approval modal and approve (target the modal heading specifically, not the notification)
  127 |     await expect(page.locator('[role="dialog"] h2:has-text("Approve with Face ID")')).toBeVisible();
  128 |     await page.click('button:has-text("Approve")');
  129 |     
  130 |     // Wait for outcome page
  131 |     await page.waitForURL('**/payment/outcome');
  132 |     
  133 |     // Verify outcome page shows payment result
  134 |     await expect(page.locator('h1')).toHaveText(/Payment sent|Payment pending|Payment not sent/);
  135 |   });
  136 | 
  137 |   test('should enforce reference character limit of 18', async ({ page }) => {
  138 |     // Select a payee and navigate to payment entry
  139 |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  140 |     await page.click('button:has-text("Continue to payment")');
  141 |     await page.waitForURL('**/payment/entry');
  142 |     
  143 |     // Try to enter more than 18 characters
  144 |     const referenceInput = page.locator('#reference');
  145 |     await referenceInput.fill('123456789012345678901234567890');
  146 |     
  147 |     // Verify only 18 characters are accepted
  148 |     await expect(referenceInput).toHaveValue('123456789012345678');
  149 |   });
  150 | 
  151 |   test('should show info notification about Face ID approval', async ({ page }) => {
  152 |     // Select a payee and navigate to payment entry
  153 |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  154 |     await page.click('button:has-text("Continue to payment")');
  155 |     await page.waitForURL('**/payment/entry');
  156 |     
  157 |     // Verify info notification present
  158 |     await expect(page.locator('text=You\'ll approve with Face ID')).toBeVisible();
  159 |     await expect(page.locator('text=/Your approval is tied to/i')).toBeVisible();
  160 |   });
  161 | });
  162 | 
```