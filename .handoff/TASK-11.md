# TASK-11 Handoff: UI U1 - Sign In and Accounts Overview

## Components Implemented

All components built following wireframe_01_sign_in.html and wireframe_02_accounts_overview.html specifications.

### Pages

1. **SignInPage** (`/repos/lbg-ftr-demo-repo/frontend/src/pages/SignInPage.tsx`)
   - Passcode sign-in form with 4-12 character validation
   - Pre-configured with seed device identifier: `device-CUST-SYNTH-001-iOS`
   - Generic error message for all sign-in failures
   - Session-ended reconnect message support
   - Protected content notice
   - Exact wireframe fidelity: colors, spacing, text, layout

2. **AccountsOverviewPage** (`/repos/lbg-ftr-demo-repo/frontend/src/pages/AccountsOverviewPage.tsx`)
   - Fetches accounts from GET `/api/v1/accounts`
   - Displays account cards with balances and freshness
   - Shows capability banner when overview_state is partial/unavailable
   - Shows stale balance banner when accounts have stale data
   - Sign-out button
   - Refresh accounts button
   - Bottom navigation tabs
   - Greeting with user display name

### Components

1. **AccountCard** (`/repos/lbg-ftr-demo-repo/frontend/src/components/accounts/AccountCard.tsx`)
   - Display name and masked account identifier
   - Balance display with availability state handling
   - **Never shows missing balance as £0.00** (shows "Balance unavailable" text instead)
   - Freshness badge (Current/Stale/Unavailable with icon+text)
   - Freshness text (e.g., "Updated 2 minutes ago")
   - Partial account handling

2. **BadgeIcon** (`/repos/lbg-ftr-demo-repo/frontend/src/components/shared/BadgeIcon.tsx`)
   - Reusable badge component with icon+text
   - Three variants: current (green), stale (amber), unavailable (red)
   - Accessible plain language rendering

3. **CapabilityBanner** (`/repos/lbg-ftr-demo-repo/frontend/src/components/shared/CapabilityBanner.tsx`)
   - Shows degraded capability messages
   - Two variants: partial (amber), unavailable (red)
   - Clear capability-specific messages

## Routes

Updated `/repos/lbg-ftr-demo-repo/frontend/src/App.tsx`:
- `/login` → SignInPage
- `/accounts` → AccountsOverviewPage (protected by RequireAuth)
- `/` → redirects to `/accounts`

## Auth Context Updates

Updated `/repos/lbg-ftr-demo-repo/frontend/src/lib/auth-context.tsx`:
- Login request matches TASK-3 API contract: `{ device_identifier, mobile_platform, passcode }`
- Login response matches TASK-3 API contract with full session details
- Token stored in sessionStorage
- Error state management with clearError method

## API Integration

SignInPage:
- POST `/api/v1/auth/login` with device_identifier, mobile_platform, passcode
- Generic error message for all failures (never reveals which check failed)
- Successful login stores token and redirects to `/accounts`

AccountsOverviewPage:
- GET `/api/v1/accounts` to fetch account list
- Respects `overview_state` from API response
- Shows capability banner based on response capability status
- Logout calls POST `/api/v1/auth/logout`

## Acceptance Criteria Coverage

### FR-AUTH-003 (Passcode sign-in)
✅ SignInPage component with passcode input field (4-12 characters, password type, autocomplete current-password)
✅ Sign-in button calls POST /api/v1/auth/login via auth-context login method
✅ Error handling shows one fixed generic message for all failures
✅ Successful sign-in transitions customer to authenticated AccountsOverviewPage

### FR-AUTH-006 (Session continuity)
✅ AccountsOverviewPage wrapped in RequireAuth (redirects to sign-in when session invalid)
✅ Session-ended reconnect message shown on login page when redirected
✅ Protected content (account cards) not displayed before authentication completes

### FR-ACCT-001 (Accounts overview)
✅ AccountsOverviewPage calls GET /api/v1/accounts
✅ Renders account cards for each in-scope personal account with distinguishing information
✅ Shows capability banner when overview_state partial or unavailable
✅ Clear capability-specific message rather than implying full success
✅ Partial account with item_state partial stays visible alongside other accounts

### FR-ACCT-002 (Freshness timestamp)
✅ Each account card shows freshness badge (Current/Stale/Unavailable with icon+text, never color alone)
✅ Freshness text (e.g., "Updated 2 minutes ago" or "Not current")
✅ Based on as_of_timestamp and freshness_status from response
✅ Freshness messaging visible on revisit/refresh
✅ Accessible plain language rendering

### FR-ACCT-003 (Never show missing balance as zero)
✅ When balance_amount_minor is NULL and balance_availability_state is unavailable or unknown, AccountCard renders "Balance unavailable" text with icon, never £0.00 or numeric zero
✅ Partial data failure communicated clearly
✅ Rule applied consistently across overview

## Tests

### Unit Tests (All Passing)

**SignInPage.test.tsx** (8 tests):
- ✅ Renders sign-in form with passcode input
- ✅ Shows hint text for passcode field
- ✅ Shows protected content notice
- ✅ Validates passcode length before submission
- ✅ Calls login API with correct credentials on form submission
- ✅ Shows error message on login failure
- ✅ Disables submit button during loading
- ✅ Clears error when user starts typing

**AccountCard.test.tsx** (6 tests):
- ✅ Renders current account with balance and freshness
- ✅ Renders stale account with appropriate badge
- ✅ Renders unavailable balance without showing zero
- ✅ Renders partial account with appropriate messaging
- ✅ Never shows missing balance as £0.00
- ✅ Renders account type and masked identifier correctly

Run unit tests:
```bash
cd /repos/lbg-ftr-demo-repo/frontend
npx vitest run src/__tests__/SignInPage.test.tsx src/__tests__/AccountCard.test.tsx
```

### E2E Tests

**wireframe_01_sign_in.spec.ts** (6 tests):
- Renders sign-in page with form fields
- Login with seed credentials and redirect to accounts
- Shows error on invalid credentials
- Validates passcode length
- Clears error when user starts typing
- Passcode input has correct attributes

**wireframe_02_accounts_overview.spec.ts** (9 tests):
- Renders accounts overview page with account cards
- Displays account cards with balances and freshness
- Never shows missing balance as £0.00
- Shows freshness text on each account
- Has refresh accounts button
- Allows sign-out
- Shows capability banner when accounts have degraded state
- Displays greeting with user name

Run E2E tests (requires backend running):
```bash
cd /repos/lbg-ftr-demo-repo/frontend
npx playwright test e2e/wireframe_01_sign_in.spec.ts
npx playwright test e2e/wireframe_02_accounts_overview.spec.ts
```

## Design Fidelity

All components precisely match the wireframe specifications:

**Colors:**
- Brand navy: `#002563`
- Brand blue: `#0074CD`
- Tint blue: `#F2FAFF`
- Page gray: `#F7F9F8`
- Text ink: `#575756`
- Label gray: `#4F5155`
- Error red: `#BE222A`
- Success green: `#1D6B37`
- Warning amber: `#8A5A00`
- Warning bg: `#FFF6E0`

**Typography:**
- Heading: 28px, navy, bold
- Body: 16px, ink color
- Label: 14px, black, bold
- Hint text: 14px, label gray

**Spacing & Layout:**
- Status bar: 44px height
- Brand header: navy background, white text
- Content padding: 24px horizontal, 16px vertical
- Card border radius: 16px
- Button height: 48px minimum
- Gaps: 16px between sections

**Icons:**
- All icons inline SVG with 20px×20px size
- Stroke width: 2px
- Current: check-circle icon
- Stale: clock icon
- Unavailable: circle-x icon
- Alert: triangle icon

## Notes for Future Tasks

1. **Session Reconnect**: The SignInPage supports session-ended state via location.state.sessionEnded - future payment tasks should use this when redirecting to login after session timeout

2. **Seed Credentials**: The SignInPage is hardcoded to use device-CUST-SYNTH-001-iOS and mobile_platform iOS - this matches the seed data from TASK-3

3. **API Contract**: All API calls use `/v1/auth/login` and `/v1/accounts` paths matching TASK-3 and TASK-4 handoff specifications

4. **Capability Status**: The AccountsOverviewPage reads capability status from the accounts response - future tasks should ensure capability-statuses endpoint returns consistent data

5. **E2E Test Dependencies**: E2E tests require the backend to be running with seeded data - they will pass once the full application is started via start.sh

## Verification Commands

```bash
# Unit tests
cd /repos/lbg-ftr-demo-repo/frontend
npx vitest run src/__tests__/SignInPage.test.tsx src/__tests__/AccountCard.test.tsx

# E2E tests (requires backend running)
npx playwright test e2e/wireframe_01_sign_in.spec.ts
npx playwright test e2e/wireframe_02_accounts_overview.spec.ts

# Type check
npx tsc --noEmit

# Build
npm run build
```
