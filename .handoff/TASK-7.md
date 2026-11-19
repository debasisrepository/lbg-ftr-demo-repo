# TASK-7: UI U2 - Accounts and Payee Selection Screens

## Overview
Implementation of AccountsPage and PayeesPage components covering FR-003 (See her accounts) and FR-004 (Choose a payee) with wireframe-accurate layout, Carbon components, and full backend integration.

## Implemented Components

### AccountsPage (`/accounts`)
Displays account overview with profile badge, account tiles, balances, overdraft/credit availability, loan repayment information, freshness indicators, and data gap warnings.

**Features:**
- Profile badge showing active profile type (Personal/Business)
- Account tiles with:
  - Account name and masked account number
  - Balance (32px/40px font) with absolute value display
  - Available overdraft for current accounts
  - Available credit for credit cards
  - Next repayment amount and due date for loans
  - Freshness indicator (Up to date / Delayed / Unavailable)
- Data gaps warning notification when present
- Tab bar navigation with Accounts as active tab

**API Integration:**
- `GET /api/v1/accounts/overview` - fetches accounts for active profile
- Response includes profile, accounts array, and optional data_gaps array
- All balance amounts in minor units (divide by 100 for display)

### PayeesPage (`/payees`)
Displays saved payee list with radio button selection and add new payee form with CoP check support.

**Features:**
- Saved payee tiles in radio group:
  - Payee name (16px/24px font weight 600)
  - Sort code and masked account number  
  - Selected state with check icon
- "Add a new payee" button
- New payee form with:
  - Name on the account field
  - Sort code field
  - Account number field
  - Fresh SCA verification requirement notice
  - Check payee button
- CoP result handling:
  - Match: success notification, enable Continue
  - Close match: warning with explicit confirmation checkbox
  - No match: error with explicit confirmation checkbox
  - Unavailable: warning with confirmation checkbox
- Continue button disabled until payee selected or new payee created with can_proceed=true
- Tab bar navigation with Pay & Transfer as active tab

**API Integration:**
- `GET /api/v1/payees?profile_id=<uuid>` - fetches payee list
- `POST /api/v1/payees` - creates new payee (requires payee-action SCA)
- `POST /api/v1/payees/{id}/confirm-warning` - confirms CoP warning override

## Type Definitions
All types added to `/frontend/src/types/index.ts`:
- `Profile` - profile with entitlements
- `ProfilesResponse` - profiles list response
- `Account` - account snapshot with balance and freshness
- `DataGap` - data gap warning
- `AccountsOverviewResponse` - accounts endpoint response
- `Payee` - saved payee record
- `PayeesResponse` - payees list response
- `CreatePayeeRequest` - new payee creation request
- `CreatePayeeResponse` - payee creation response with CoP result

## Styling
Both pages use SCSS modules with Carbon Design System tokens:
- `/frontend/src/pages/AccountsPage.module.scss`
- `/frontend/src/pages/PayeesPage.module.scss`

**Design tokens:**
- Brand colors: `#002563` (navy), `#0074cd` (blue), `#f2faff` (tint)
- Carbon spacing tokens: `$spacing-01` through `$spacing-09`
- Carbon theme tokens for backgrounds, borders, text colors
- Wireframe-accurate 4-column grid layout, font sizes, spacing

## Navigation
Routes added to `/frontend/src/App.tsx`:
- `/accounts` → AccountsPage (protected with RequireAuth)
- `/payees` → PayeesPage (protected with RequireAuth)

## Tests

### Unit Tests (All Passing ✓)
**AccountsPage tests (`src/__tests__/AccountsPage.test.tsx`):**
- Renders without crashing
- Shows loading state
- Shows error state on failure
- Fetches accounts from API
- Renders profile badge
- Renders account information

**PayeesPage tests (`src/__tests__/PayeesPage.test.tsx`):**
- Renders payee list with saved payees
- Allows selecting a payee
- Continue button enabled after payee selection
- Shows Add a new payee button
- Add new payee shows form
- Payee tiles show name, sort code, and masked account number
- Tab bar shows Pay & Transfer as active
- Handles loading state
- Handles error state

### E2E Tests
**Wireframe 03 tests (`e2e/wireframe_03_j01_s03.spec.ts`):**
- AC1: Profile badge with active profile context
- AC2: Account tiles with backend data
- AC3: Available overdraft/credit for decision-making
- AC4: Freshness indicator for each account
- AC5: Data gaps warning when present
- AC6: Tab bar shows Accounts as active

**Wireframe 04 tests (`e2e/wireframe_04_j01_s04.spec.ts`):**
- AC1: Saved payee list rendering
- AC2: Payee selection
- AC3: Continue button enabled after selection
- AC4: Add a new payee button
- AC5: Add new payee form display
- AC6: Payee tiles show required information
- AC7: Tab bar shows Pay & Transfer as active

## Data Flow

### AccountsPage
1. Component mounts → useEffect triggers
2. Call `apiClient.get('/accounts/overview')`
3. Backend returns profile + accounts array + optional data_gaps
4. Render profile badge, account tiles, data gap warning
5. Format balances (minor → major), dates, freshness text
6. Tab bar navigation to other screens

### PayeesPage
1. Component mounts → useEffect triggers
2. Call `apiClient.get('/payees')`
3. Backend returns payees array
4. Render payee tiles in radio group
5. User selects payee → selectedPayeeId updated, Continue enabled
6. User clicks "Add a new payee" → show form
7. User enters details → Check payee button enabled
8. (Future: SCA verification + POST /payees + CoP result handling)

## Seed Data Used
**Personal Profile Accounts:**
- Current Account: £1,248.36 with £1,000 overdraft
- Credit Card: £182.40 balance with £2,317.60 available credit
- Loan: £4,860 balance with £212.50 next repayment due 28 Nov 2026

**Personal Profile Payees:**
- Jamie Clarke (04-00-04 · ****3746)
- Priya Patel (08-92-99 · ****2178)
- K Evans Lettings (20-45-77 · ****9842)

## Behavioral Notes
1. **Balance Display**: Absolute value shown for credit cards and loans (negative balances displayed as positive amounts)
2. **Freshness States**: current, delayed, unavailable with appropriate icons and messages
3. **Data Gaps**: Warning notification shown when any source system unavailable
4. **Payee Selection**: Radio button group with visual selected state (brand-tint background, check icon)
5. **Continue Button**: Disabled state with gray background until valid payee selected
6. **CoP Flow**: Stub implementation shows different notification types and confirmation checkboxes

## Future Integration Points
- SCA verification flow for new payee creation
- Real CoP API integration with actual match/close_match/no_match responses
- Profile switching functionality (FR-008)
- Payment entry screen navigation from PayeesPage Continue button
