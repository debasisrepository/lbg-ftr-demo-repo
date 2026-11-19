# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: wireframe_06_j01_s06.spec.ts >> Wireframe 06 - Payment Outcome (FR-006) >> should display sent payment outcome with all required details
- Location: e2e/wireframe_06_j01_s06.spec.ts:32:3

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Approve with Face ID')
Expected: visible
Error: strict mode violation: locator('text=Approve with Face ID') resolved to 2 elements:
    1) <div dir="auto" class="cds--inline-notification__title">You'll approve with Face ID</div> aka getByText('You\'ll approve with Face ID')
    2) <h2 dir="auto" class="cds--modal-header__heading" id="cds--modal-header__heading--modal-id-:rn:">Approve with Face ID</h2> aka getByText('Approve with Face ID', { exact: true })

Call log:
  - Expect "toBeVisible" locator('text=Approve with Face ID') with timeout 5000ms
  - waiting for locator('text=Approve with Face ID')

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
  3   | test.describe('Wireframe 06 - Payment Outcome (FR-006)', () => {
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
  32  |   test('should display sent payment outcome with all required details', async ({ page }) => {
  33  |     // Select a payee and navigate to payment entry
  34  |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  35  |     await page.click('button:has-text("Continue to payment")');
  36  |     await page.waitForURL('**/payment/entry');
  37  |     
  38  |     // Enter valid payment details
  39  |     const amountInput = page.locator('#amount');
  40  |     await amountInput.clear();
  41  |     await amountInput.fill('50.00');
  42  |     
  43  |     const referenceInput = page.locator('#reference');
  44  |     await referenceInput.fill('Test payment');
  45  |     
  46  |     // Click pay button and approve
  47  |     await page.click('button:has-text("Pay £50.00")');
> 48  |     await expect(page.locator('text=Approve with Face ID')).toBeVisible();
      |                                                             ^ Error: expect(locator).toBeVisible() failed
  49  |     await page.click('button:has-text("Approve")');
  50  |     
  51  |     // Wait for outcome page
  52  |     await page.waitForURL('**/payment/outcome');
  53  |     
  54  |     // Verify outcome heading
  55  |     const heading = page.locator('h1');
  56  |     await expect(heading).toHaveText(/Payment sent|Payment pending|Payment not sent/);
  57  |     
  58  |     // Verify status badge
  59  |     await expect(page.locator('text=/^(Sent|Pending|Failed)$/i')).toBeVisible();
  60  |     
  61  |     // Verify payee name in summary
  62  |     await expect(page.locator('dt:has-text("Payee") + dd')).toHaveText('Jamie Clarke');
  63  |     
  64  |     // Verify amount in summary
  65  |     await expect(page.locator('dt:has-text("Amount") + dd')).toHaveText('£50.00');
  66  |     
  67  |     // Verify reference in summary
  68  |     await expect(page.locator('dt:has-text("Reference") + dd')).toHaveText('Test payment');
  69  |     
  70  |     // Verify payment identifier
  71  |     await expect(page.locator('dt:has-text("Payment identifier") + dd')).toBeVisible();
  72  |   });
  73  | 
  74  |   test('should show sent status with arrival message when payment succeeds', async ({ page }) => {
  75  |     // Complete payment flow
  76  |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  77  |     await page.click('button:has-text("Continue to payment")');
  78  |     await page.waitForURL('**/payment/entry');
  79  |     
  80  |     const amountInput = page.locator('#amount');
  81  |     await amountInput.clear();
  82  |     await amountInput.fill('50.00');
  83  |     await page.click('button:has-text("Pay £50.00")');
  84  |     await page.click('button:has-text("Approve")');
  85  |     await page.waitForURL('**/payment/outcome');
  86  |     
  87  |     // Check if status is sent (70% probability from stub)
  88  |     const statusText = await page.locator('h1').textContent();
  89  |     
  90  |     if (statusText?.includes('sent')) {
  91  |       // Verify sent-specific elements
  92  |       await expect(page.locator('text=/is on its way/i')).toBeVisible();
  93  |       await expect(page.locator('text=/should arrive/i')).toBeVisible();
  94  |     }
  95  |   });
  96  | 
  97  |   test('should show pending status with duplicate warning when appropriate', async ({ page }) => {
  98  |     // Complete payment flow
  99  |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  100 |     await page.click('button:has-text("Continue to payment")');
  101 |     await page.waitForURL('**/payment/entry');
  102 |     
  103 |     const amountInput = page.locator('#amount');
  104 |     await amountInput.clear();
  105 |     await amountInput.fill('50.00');
  106 |     await page.click('button:has-text("Pay £50.00")');
  107 |     await page.click('button:has-text("Approve")');
  108 |     await page.waitForURL('**/payment/outcome');
  109 |     
  110 |     // Check if status is pending (20% probability from stub)
  111 |     const statusText = await page.locator('h1').textContent();
  112 |     
  113 |     if (statusText?.includes('pending')) {
  114 |       // Verify pending-specific elements
  115 |       await expect(page.locator('text=/waiting for confirmation/i')).toBeVisible();
  116 |       
  117 |       // Check for duplicate warning notification
  118 |       const duplicateWarning = page.locator('text=/Don\'t pay again yet/i');
  119 |       // Assert it exists when status is pending - the backend may or may not set duplicate_submission_blocked
  120 |       // but we verify the notification is present when it should be
  121 |       const isWarningVisible = await duplicateWarning.isVisible();
  122 |       // If duplicate_submission_blocked is true, warning should be visible
  123 |       // We can't control the backend stub, so we just verify the UI renders correctly when it appears
  124 |       if (isWarningVisible) {
  125 |         await expect(page.locator('text=/Paying again could send the money twice/i')).toBeVisible();
  126 |       }
  127 |     }
  128 |   });
  129 | 
  130 |   test('should show failed status with clear guidance when payment fails', async ({ page }) => {
  131 |     // Complete payment flow
  132 |     await page.click('button[role="radio"]:has-text("Jamie Clarke")');
  133 |     await page.click('button:has-text("Continue to payment")');
  134 |     await page.waitForURL('**/payment/entry');
  135 |     
  136 |     const amountInput = page.locator('#amount');
  137 |     await amountInput.clear();
  138 |     await amountInput.fill('50.00');
  139 |     await page.click('button:has-text("Pay £50.00")');
  140 |     await page.click('button:has-text("Approve")');
  141 |     await page.waitForURL('**/payment/outcome');
  142 |     
  143 |     // Check if status is failed (10% probability from stub)
  144 |     const statusText = await page.locator('h1').textContent();
  145 |     
  146 |     if (statusText?.includes('not sent')) {
  147 |       // Verify failed-specific elements
  148 |       await expect(page.locator('text=/We couldn\'t send/i')).toBeVisible();
```