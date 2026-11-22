/**
 * Pay & Transfer Hub Page
 * Implements FR-004: Payee Management
 * Wireframe: wireframe_04_j01_s04.html
 */

import { useNavigate } from 'react-router-dom'
import { usePayees } from '../features/payees/usePayees'
import { usePendingApprovals } from '../features/payments/usePendingApprovals'
import { PendingApprovalsList } from '../components/payments/PendingApprovalsList'

export function PayAndTransferPage() {
  const navigate = useNavigate()
  const { payees, loading, error } = usePayees()
  const { approvals } = usePendingApprovals()

  const handlePayeeClick = (payeeId: string) => {
    const payee = payees.find((p) => p.payee_id === payeeId)
    if (payee) {
      navigate('/pay', {
        state: {
          payee_id: payee.payee_id,
          payee_name: payee.payee_name,
          sort_code: payee.sort_code,
          account_number_masked: payee.account_number_masked,
        },
      })
    }
  }

  const handleAddPayee = () => {
    navigate('/add-payee')
  }

  const handleApprovalClick = (paymentOrderId: string) => {
    // Navigate to payment approval/review screen
    navigate(`/payment/review`, { state: { payment_order_id: paymentOrderId } })
  }

  const handleIncidentReport = () => {
    navigate('/support/incident-report')
  }

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', background: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p>Loading...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ minHeight: '100vh', background: '#ffffff', padding: '24px' }}>
        <p style={{ color: '#c62828' }}>Error: {error}</p>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#ffffff', display: 'flex', flexDirection: 'column' }}>
      {/* Status bar */}
      <div style={{ height: '44px', flexShrink: 0, display: 'flex', alignItems: 'center', padding: '0 24px', fontSize: '14px', fontWeight: 600 }}>
        9:41
      </div>

      {/* Content */}
      <div style={{ flex: '1 0 auto', padding: '8px 24px 24px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ margin: '16px 0 24px', fontSize: '28px', lineHeight: '36px', fontWeight: 600 }}>
          Pay &amp; Transfer
        </h2>

        {/* Pending Approvals for Business Payments */}
        <PendingApprovalsList approvals={approvals} onApprovalClick={handleApprovalClick} />

        <h3 style={{ margin: '12px 0 8px', fontSize: '20px', lineHeight: '28px', fontWeight: 600 }}>
          Pay someone
        </h3>

        <div style={{ borderTop: '1px solid #c6c6c6', marginBottom: '24px' }}>
          {payees.map((payee) => (
            <button
              key={payee.payee_id}
              onClick={() => handlePayeeClick(payee.payee_id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                minHeight: '64px',
                padding: '12px 0',
                width: '100%',
                border: 'none',
                borderBottom: '1px solid #c6c6c6',
                background: 'transparent',
                textAlign: 'left',
                cursor: 'pointer',
              }}
            >
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <strong style={{ fontWeight: 600, fontSize: '16px' }}>{payee.payee_name}</strong>
                <span style={{ fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
                  {payee.sort_code} · {payee.account_number_masked}
                </span>
              </div>
              <svg
                viewBox="0 0 24 24"
                style={{ width: '20px', height: '20px', stroke: '#161616', fill: 'none', strokeWidth: 2 }}
                aria-hidden="true"
              >
                <path d="M9 5l7 7-7 7" />
              </svg>
            </button>
          ))}

          <button
            onClick={handleAddPayee}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              minHeight: '64px',
              padding: '12px 0',
              width: '100%',
              border: 'none',
              borderBottom: '1px solid #c6c6c6',
              background: 'transparent',
              textAlign: 'left',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <strong style={{ fontWeight: 600, textDecoration: 'underline' }}>Add a new payee</strong>
            </div>
            <svg
              viewBox="0 0 24 24"
              style={{ width: '20px', height: '20px', stroke: '#161616', fill: 'none', strokeWidth: 2 }}
              aria-hidden="true"
            >
              <path d="M12 5v14M5 12h14" />
            </svg>
          </button>
        </div>

        <h3 style={{ margin: '12px 0 8px', fontSize: '20px', lineHeight: '28px', fontWeight: 600 }}>
          Move money
        </h3>

        <div style={{ borderTop: '1px solid #c6c6c6' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              minHeight: '64px',
              padding: '12px 0',
              borderBottom: '1px solid #c6c6c6',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <strong style={{ fontWeight: 600 }}>Pay your credit card</strong>
              <span style={{ fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
                Balance £182.40
              </span>
            </div>
            <svg
              viewBox="0 0 24 24"
              style={{ width: '20px', height: '20px', stroke: '#161616', fill: 'none', strokeWidth: 2 }}
              aria-hidden="true"
            >
              <path d="M9 5l7 7-7 7" />
            </svg>
          </div>
        </div>

        {/* Help & Support Section */}
        <h3 style={{ margin: '24px 0 8px', fontSize: '20px', lineHeight: '28px', fontWeight: 600 }}>
          Help &amp; Support
        </h3>

        <div style={{ borderTop: '1px solid #c6c6c6' }}>
          <button
            onClick={handleIncidentReport}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              minHeight: '64px',
              padding: '12px 0',
              width: '100%',
              border: 'none',
              borderBottom: '1px solid #c6c6c6',
              background: 'transparent',
              textAlign: 'left',
              cursor: 'pointer',
            }}
          >
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <strong style={{ fontWeight: 600 }}>Report an issue</strong>
              <span style={{ fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
                Technical problems or service issues
              </span>
            </div>
            <svg
              viewBox="0 0 24 24"
              style={{ width: '20px', height: '20px', stroke: '#161616', fill: 'none', strokeWidth: 2 }}
              aria-hidden="true"
            >
              <path d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>

        <div style={{ flex: '1 0 0' }} />
      </div>

      {/* Tab bar */}
      <nav style={{ flexShrink: 0, display: 'flex', borderTop: '1px solid #c6c6c6', background: '#ffffff' }} aria-label="Main">
        <button
          onClick={() => navigate('/accounts')}
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
            <rect x="3" y="6" width="18" height="13" />
            <path d="M3 10h18" />
          </svg>
          Accounts
        </button>
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
            <path d="M4 8h14l-4-4M20 16H6l4 4" />
          </svg>
          Pay &amp; Transfer
        </div>
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
