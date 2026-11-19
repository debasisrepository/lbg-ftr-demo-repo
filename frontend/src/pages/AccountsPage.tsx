/**
 * Accounts Overview Page
 * Implements FR-003: Accounts and Loans Aggregation
 * Wireframe: wireframe_03_j01_s03.html
 */

import { useNavigate } from 'react-router-dom'
import { useAccountsOverview, AccountOverview, LoanOverview } from '../features/accounts/useAccountsOverview'
import { useProfiles } from '../features/accounts/useProfiles'
import { ProfileSwitcher } from '../components/accounts/ProfileSwitcher'
import { StatusBanner } from '../components/accounts/StatusBanner'
import { formatMinor } from '../lib/money'

export function AccountsPage() {
  const navigate = useNavigate()
  const { data: accountsData, loading: accountsLoading, error: accountsError, refetch } = useAccountsOverview()
  const { profiles, setActiveProfile } = useProfiles()

  const handleSignOut = () => {
    localStorage.clear()
    sessionStorage.clear()
    navigate('/login', { replace: true })
  }

  const handleProfileChange = async (profileId: string) => {
    try {
      await setActiveProfile(profileId)
      await refetch()
    } catch (err) {
      console.error('Failed to switch profile:', err)
    }
  }

  const renderAccountCard = (account: AccountOverview) => {
    const isUnavailable = account.source_status === 'unavailable' || account.current_balance_minor === null
    const isStale = account.source_status === 'stale'
    const isCreditCard = account.account_type === 'credit_card'

    return (
      <div
        key={account.bank_account_id}
        style={{
          border: '1px solid #8d8d8d',
          borderLeft: isUnavailable ? '4px solid #161616' : '1px solid #8d8d8d',
          background: '#ffffff',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        <h3 style={{ margin: 0, fontSize: '16px', lineHeight: '24px', fontWeight: 600 }}>
          {account.account_name}
        </h3>
        {account.sort_code_masked && account.account_number_masked && (
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
            {account.sort_code_masked} | {account.account_number_masked}
          </p>
        )}
        {isCreditCard && account.account_number_masked && (
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
            {account.account_number_masked}
          </p>
        )}
        <p style={{ margin: '12px 0 0', fontSize: '28px', lineHeight: '36px', fontWeight: 600 }}>
          {isUnavailable ? 'Unavailable' : formatMinor(account.current_balance_minor || 0, account.currency_code)}
        </p>
        {!isUnavailable && account.available_balance_minor !== null && account.overdraft_limit_minor !== null && (
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px', color: '#393939' }}>
            Available overdraft: {formatMinor(account.overdraft_limit_minor, account.currency_code)}
          </p>
        )}
        {!isUnavailable && isCreditCard && account.available_balance_minor !== null && (
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px', color: '#393939' }}>
            Available credit: {formatMinor(account.available_balance_minor, account.currency_code)}
          </p>
        )}
        {isUnavailable && (
          <p style={{ margin: '12px 0 0', fontSize: '14px', fontWeight: 600, color: '#c62828' }}>
            Error: We can't show this balance right now. Try again shortly.
          </p>
        )}
        {isStale && account.freshness_at && (
          <p style={{ margin: 0, fontSize: '12px', lineHeight: '18px', color: '#525252' }}>
            Balance as at {new Date(account.freshness_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })} today
          </p>
        )}
      </div>
    )
  }

  const renderLoanCard = (loan: LoanOverview) => {
    const isUnavailable = loan.source_status === 'unavailable' || loan.outstanding_balance_minor === null

    return (
      <div
        key={loan.loan_snapshot_id}
        style={{
          border: '1px solid #8d8d8d',
          background: '#ffffff',
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        <h3 style={{ margin: 0, fontSize: '16px', lineHeight: '24px', fontWeight: 600 }}>
          {loan.loan_name}
        </h3>
        {loan.external_loan_ref && (
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
            Loan ending {loan.external_loan_ref.slice(-4)}
          </p>
        )}
        <p style={{ margin: '12px 0 0', fontSize: '28px', lineHeight: '36px', fontWeight: 600 }}>
          {isUnavailable ? 'Unavailable' : formatMinor(loan.outstanding_balance_minor || 0, loan.currency_code)}
        </p>
        {!isUnavailable && loan.next_repayment_minor && loan.next_repayment_date && (
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px', color: '#393939' }}>
            Next repayment: {formatMinor(loan.next_repayment_minor, loan.currency_code)} due{' '}
            {new Date(loan.next_repayment_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short' })}
          </p>
        )}
      </div>
    )
  }

  if (accountsLoading) {
    return (
      <div style={{ minHeight: '100vh', background: '#f3f4f6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>Loading...</p>
      </div>
    )
  }

  if (accountsError) {
    return (
      <div style={{ minHeight: '100vh', background: '#f3f4f6', padding: '24px' }}>
        <StatusBanner message={`Error: ${accountsError}`} type="warning" />
      </div>
    )
  }

  const firstName = accountsData?.profile_display_name?.split(' ')[0] || 'there'

  return (
    <div style={{ minHeight: '100vh', background: '#f3f4f6', display: 'flex', flexDirection: 'column' }}>
      {/* Status bar */}
      <div style={{ height: '44px', flexShrink: 0, display: 'flex', alignItems: 'center', padding: '0 24px', fontSize: '14px', fontWeight: 600, background: '#ffffff' }}>
        9:41
      </div>

      {/* Header */}
      <div style={{ minHeight: '56px', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 8px 0 24px', borderBottom: '1px solid #c6c6c6', background: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, fontSize: '18px' }}>
          <div style={{ width: '28px', height: '28px', border: '2px solid #161616', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 600 }}>
            YB
          </div>
          Your Bank
        </div>
        <button
          onClick={handleSignOut}
          style={{ width: '44px', height: '44px', border: 0, background: 'transparent', cursor: 'pointer' }}
          aria-label="Menu"
        >
          <svg viewBox="0 0 24 24" style={{ width: '24px', height: '24px', stroke: '#161616', fill: 'none', strokeWidth: 2 }}>
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: '1 0 auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <p style={{ margin: 0, fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
            Hello, {firstName}
          </p>
          <h2 style={{ margin: 0, fontSize: '28px', lineHeight: '36px', fontWeight: 600 }}>
            Your accounts
          </h2>
        </div>

        {profiles.length > 1 && accountsData && (
          <ProfileSwitcher
            profiles={profiles}
            activeProfileId={accountsData.profile_id}
            onProfileChange={handleProfileChange}
          />
        )}

        {accountsData?.accounts?.map(renderAccountCard)}
        {accountsData?.loans?.map(renderLoanCard)}
      </div>

      {/* Tab bar */}
      <nav style={{ flexShrink: 0, display: 'flex', borderTop: '1px solid #c6c6c6', background: '#ffffff' }} aria-label="Main">
        <div
          style={{
            flex: 1,
            minHeight: '64px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            lineHeight: '16px',
            color: '#161616',
            fontWeight: 600,
            gap: '4px',
            boxShadow: 'inset 0 3px 0 #161616',
          }}
          aria-current="page"
        >
          <svg viewBox="0 0 24 24" style={{ width: '24px', height: '24px', stroke: 'currentColor', fill: 'none', strokeWidth: 2 }}>
            <rect x="3" y="6" width="18" height="13" />
            <path d="M3 10h18" />
          </svg>
          Accounts
        </div>
        <button
          onClick={() => navigate('/pay-and-transfer')}
          style={{
            flex: 1,
            minHeight: '64px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '12px',
            lineHeight: '16px',
            color: '#525252',
            gap: '4px',
            border: 'none',
            background: 'transparent',
            cursor: 'pointer',
          }}
        >
          <svg viewBox="0 0 24 24" style={{ width: '24px', height: '24px', stroke: 'currentColor', fill: 'none', strokeWidth: 2 }}>
            <path d="M4 8h14l-4-4M20 16H6l4 4" />
          </svg>
          Pay &amp; Transfer
        </button>
        <div style={{ flex: 1, minHeight: '64px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontSize: '12px', lineHeight: '16px', color: '#525252', gap: '4px' }}>
          <svg viewBox="0 0 24 24" style={{ width: '24px', height: '24px', stroke: 'currentColor', fill: 'none', strokeWidth: 2 }}>
            <rect x="4" y="4" width="7" height="7" />
            <rect x="13" y="4" width="7" height="7" />
            <rect x="4" y="13" width="7" height="7" />
            <rect x="13" y="13" width="7" height="7" />
          </svg>
          Products
        </div>
        <div style={{ flex: 1, minHeight: '64px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', fontSize: '12px', lineHeight: '16px', color: '#525252', gap: '4px' }}>
          <svg viewBox="0 0 24 24" style={{ width: '24px', height: '24px', stroke: 'currentColor', fill: 'none', strokeWidth: 2 }}>
            <circle cx="5" cy="12" r="1.5" />
            <circle cx="12" cy="12" r="1.5" />
            <circle cx="19" cy="12" r="1.5" />
          </svg>
          More
        </div>
      </nav>
    </div>
  )
}
