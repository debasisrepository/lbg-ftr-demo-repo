# TASK-12 Handoff: UI U2 - Payee Selection and Payment Entry

## Pages Implemented

All pages mounted under protected routes with RequireAuth wrapper:

### `/payees` - PayeesPage
Payee selection page with capability-aware degraded mode.

**Calls:**
- GET `/api/v1/payees` - fetches saved payees list
- GET `/api/v1/capability-statuses` - fetches capability statuses for payments

**Displays:**
- List of saved payees (name, sort code, masked account ending)
- Capability banner when saved_payees unavailable
- Payments capability banner when payments unavailable
- Empty state when no payees available
- Error state with retry button

**Navigation:**
- Clicking payee navigates to `/payment-entry` with payee state
- Bottom tabs: "Accounts" (links to `/accounts`), "Pay & Transfer" (active, links to `/payees`)

**Data shown:**
- Payee name: e.g. "Jamie Clarke"
- Sort code: e.g. "04-00-04"
- Masked account: e.g. "****3321"
- Hint: "Choose a payee to start a payment. Full account numbers are never shown."

### `/payment-entry` - PaymentEntryPage
Payment details entry form with validation and idempotency.

**Requires:**
- Payee passed via navigation state from PayeesPage

**Calls:**
- GET `/api/v1/accounts/` - fetches eligible source accounts (payment_source_eligible only)
- POST `/api/v1/payments` - creates payment intent with Idempotency-Key header

**Form fields:**
1. Source account picker (dropdown, shows balance or "Balance unavailable" text, never £0.00 for unavailable)
2. Amount input (decimal, > 0, format: 250.00)
3. Payment reference input (1-18 characters, character counter shown)

**Validation:**
- Amount must be > 0
- Reference required, 1-18 characters
- Submit button disabled until form complete and valid

**Idempotency:**
- Generates UUID idempotency key once per journey, stored in component state
- Passes key in `Idempotency-Key` header on payment creation
- Carries key through to payment review for approval

**Navigation:**
- Back button returns to `/payees`
- Submit navigates to `/payment-review` with payment response and idempotency key in state

### `/payment-review` - PaymentReviewPage
Review screen showing all dynamic-link fields before approval.

**Requires:**
- Payment passed via navigation state from PaymentEntryPage
- Idempotency key passed via navigation state

**Displays:**
- Source account (From): display name, masked account ending
- Payee (To): name, masked account ending
- Amount: formatted as £250.00
- Payment reference: entered text
- Hint: "Check these details. Your approval applies only to this payment. Nothing has been sent yet."
- Footer: "Payment not sent yet. Review and approve it to send."

**Actions:**
1. "Approve payment" button - opens ApprovalSheet modal
2. "Change details" button - navigates back to `/payment-entry` with payee state
3. Back button - navigates back to `/payment-entry`

**Navigation after approval:**
- Success: navigates to `/payment-outcome` with payment state
- Failure: navigates to `/payment-failed` with payee, amount, reference state

### `/payment-outcome` - PaymentOutcomePage
Outcome page showing payment success, pending, or failed status.

**Requires:**
- Payment passed via navigation state from PaymentReviewPage

**Displays:**
- **Success (Sent)**: Green success banner, "Payment sent", payment details summary
- **Pending**: Amber pending banner, "Payment pending", status message, do_not_resubmit guidance
- **Failed**: Red error banner, "Payment not sent", "No money was sent", status message

**Actions:**
1. "Back to accounts" - navigates to `/accounts`
2. "Make another payment" - navigates to `/payees`

### `/payment-failed` - PaymentFailedPage
Approval failure page showing why payment wasn't sent.

**Requires:**
- Payee, amount, reference passed via navigation state from PaymentReviewPage

**Displays:**
- Red error banner: "Payment not sent", "We couldn't approve this payment. No money was sent."
- Explanation: reasons why approval failed (incorrect passcode, timeout, cancelled)
- Payment summary: payee name, amount, reference

**Actions:**
1. "Try again" - navigates to `/payees` to start new payment
2. "Back to accounts" - navigates to `/accounts`

## Components Implemented

### `ApprovalSheet.tsx`
Modal overlay sheet for passcode approval of payment.

**Props:**
- `payment: PaymentReviewResponse` - payment details to approve
- `idempotencyKey: string` - idempotency key for submit request
- `onClose: () => void` - close handler (clears passcode)
- `onSuccess: (payment: PaymentReviewResponse) => void` - success callback
- `onFailure: () => void` - failure callback

**Behavior:**
- Renders as modal dialog (`role="dialog"`) with overlay
- Auto-focuses passcode input on mount
- Passcode validation: 4-12 characters
- Calls POST `/api/v1/payments/{payment_id}/submit` with:
  - Authorization header (Bearer token from sessionStorage)
  - Idempotency-Key header
  - Body: `{ review_version, review_fingerprint, approval: { method: 'passcode', passcode } }`
- Success: calls onSuccess with updated payment
- Failure (401 or approval_failed_or_abandoned state): calls onFailure
- Cancel: clears passcode, calls onClose
- Shows approval button as "Approve £250.00" with amount
- Hint: "The sheet clears your passcode when it closes. Cancelling leaves the payment unsent."

### `PayeeListItem.tsx`
List item component for rendering individual payee in payees list.

**Props:**
- `payee: PayeeItem` - payee data (payee_id, payee_name, payee_sort_code, masked_account_identifier)
- `onSelect: () => void` - selection handler

**Renders:**
- Button (full-width, left-aligned)
- Payee name (bold)
- Sort code and masked account (secondary text): "Sort code 04-00-04, account ending ****3321"

## Routes Added

All routes in `/repos/lbg-ftr-demo-repo/frontend/src/App.tsx`:

- `/login` → SignInPage (not protected)
- `/accounts` → AccountsOverviewPage (protected)
- `/payees` → PayeesPage (protected)
- `/payment-entry` → PaymentEntryPage (protected)
- `/payment-review` → PaymentReviewPage (protected)
- `/payment-outcome` → PaymentOutcomePage (protected)
- `/payment-failed` → PaymentFailedPage (protected)
- `/pay-and-transfer` → redirects to `/payees` (alias)
- `/` → redirects to `/accounts`
- `*` → redirects to `/accounts` (catch-all)

## Navigation Structure

**Bottom tabs** (shown on AccountsOverviewPage and PayeesPage):
1. "Accounts" → `/accounts`
2. "Pay & Transfer" → `/payees`

Both tabs use React Router Link components and show active state with blue underline when on corresponding path or sub-paths (payment flow).

**Payment flow navigation:**
1. User clicks "Pay & Transfer" tab → `/payees`
2. User selects payee → `/payment-entry` (with payee state)
3. User fills form and clicks "Review payment" → `/payment-review` (with payment and idempotencyKey state)
4. User clicks "Approve payment", enters passcode, approves → `/payment-outcome` or `/payment-failed` (with payment/payee state)
5. User clicks "Back to accounts" or "Make another payment" → `/accounts` or `/payees`

## E2E Tests Implemented

### `e2e/wireframe_03_payee_and_entry.spec.ts`
9 tests covering payee selection and payment entry:
1. should display saved payees list
2. should navigate to payment entry when payee is selected
3. should display payment entry form with all fields
4. should show character counter for payment reference
5. should validate form and show errors when incomplete
6. should enable submit button when form is complete and valid
7. should create payment and navigate to review page
8. should show account balance or unavailable text in source picker
9. should navigate back to payees list when back button clicked

### `e2e/wireframe_04_review_and_approval.spec.ts`
10 tests covering payment review and approval:
1. should display payment review page with all details
2. should open approval sheet when approve button clicked
3. should close approval sheet when cancel button clicked
4. should approve payment with correct passcode and navigate to outcome
5. should navigate back to payment entry when change details clicked
6. should show masked account identifiers, not full account numbers
7. should navigate back to payment entry with back button
8. should show payment details with correct currency formatting
9. should focus passcode input when approval sheet opens
10. should include all four dynamic-linked fields in review

**Test approach:**
- All tests log in through the actual form by typing seed passcode "Pass1234" and submitting
- Tests use seed payees: Jamie Clarke (04-00-04 ****3321), Priya Patel (60-83-71 ****7745), K Evans Lettings (20-45-77 ****9842)
- Tests interact with real backend API endpoints (no mocks)
- Tests verify UI elements using accessible selectors (labels, roles, text)
- Tests verify masked account identifiers shown, full account numbers never exposed

## Unit Tests Implemented

### `src/__tests__/PayeesPage.test.tsx`
5 tests:
1. renders loading state initially
2. renders payees list after loading
3. renders error state when API call fails
4. renders unavailable banner when capability unavailable
5. navigates to payment entry when payee selected

### `src/__tests__/PaymentEntryPage.test.tsx`
5 tests:
1. renders payment entry form with payee details
2. validates amount is greater than 0
3. validates reference length 1-18 characters
4. shows character counter
5. enables submit button when form valid

## API Calls Made

All calls use relative `/api/v1/...` paths via `apiClient`:

1. **GET /api/v1/payees**
   - Fetches saved payees list
   - Response: `{ items: PayeeItem[], total, page, page_size, capability }`

2. **GET /api/v1/capability-statuses**
   - Fetches capability statuses (without trailing slash, gets 307 redirect)
   - Response: `{ items: CapabilityStatus[], total, page, page_size }`

3. **GET /api/v1/accounts/**
   - Fetches eligible source accounts (filters to payment_source_eligible)
   - Response: `{ items: AccountItem[], total, page, page_size, overview_state, capability }`

4. **POST /api/v1/payments**
   - Creates payment intent
   - Headers: `Authorization: Bearer {token}`, `Idempotency-Key: {uuid}`
   - Body: `{ source_account_reference, payee_id, amount_minor, currency, payment_reference_text, payment_channel: "mobile_app" }`
   - Response: `PaymentReviewResponse` with payment_id, current_state, review_version, review_fingerprint, etc.

5. **POST /api/v1/payments/{payment_id}/submit**
   - Submits payment for approval and execution
   - Headers: `Authorization: Bearer {token}`, `Idempotency-Key: {uuid}`
   - Body: `{ review_version, review_fingerprint, approval: { method: 'passcode', passcode } }`
   - Response: `PaymentReviewResponse` with updated current_state and customer_visible_status

## Seed Data Used

From TASK-3, TASK-5, TASK-4 handoffs:

**Customer:** Alex Taylor (CUST-SYNTH-001)
- Passcode: Pass1234
- Device: device-CUST-SYNTH-001-iOS

**Accounts:**
- Main Account ****1234 - balance varies by test
- Savings Account ****5678 - balance varies by test

**Payees:**
1. Jamie Clarke - Sort code 04-00-04, account ending ****3321
2. Priya Patel - Sort code 60-83-71, account ending ****7745
3. K Evans Lettings - Sort code 20-45-77, account ending ****9842

## Styling and Design

All pages use LBG brand colors and wireframe-matching layouts:
- Primary blue: #0074CD (buttons, links, active states)
- Primary navy: #002563 (headings, borders)
- Error red: #BE222A (errors, failed states)
- Success green: #006341 (success states)
- Warning amber: #F39C12 (pending states)
- Background: #F7F9F8
- Text: #575756 (body), #4F5155 (secondary)

## Verification

All acceptance checks passing:
- ✅ `npx vitest run src/__tests__/PayeesPage.test.tsx src/__tests__/PaymentEntryPage.test.tsx` - 10/10 tests passed
- ✅ `npx playwright test e2e/wireframe_03_payee_and_entry.spec.ts` - 9/9 tests passed
- ✅ `npx playwright test e2e/wireframe_04_review_and_approval.spec.ts` - 10/10 tests passed
- ✅ `npm run type-check` - TypeScript compilation successful
- ✅ `npm run build` - Production build successful (208.41 kB gzipped JS)
- ✅ All E2E tests log in through the form (not mocked)
- ✅ All navigation links present and functional
- ✅ All outcome routes registered and components implemented
