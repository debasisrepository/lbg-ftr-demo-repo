/**
 * Pending Approvals List Component
 * Displays business payments awaiting dual authorization (BR-ACCT-010)
 */

import { formatMinor } from '../../lib/money'
import { PendingApproval } from '../../features/payments/usePendingApprovals'

interface PendingApprovalsListProps {
  approvals: PendingApproval[]
  onApprovalClick: (paymentOrderId: string) => void
}

export function PendingApprovalsList({ approvals, onApprovalClick }: PendingApprovalsListProps) {
  if (approvals.length === 0) {
    return null
  }

  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ margin: '12px 0 8px', fontSize: '20px', lineHeight: '28px', fontWeight: 600 }}>
        Payments awaiting approval
      </h3>
      <p style={{ fontSize: '14px', color: '#525252', marginBottom: '12px' }}>
        These payments require a second approval before they can be sent.
      </p>

      <div style={{ borderTop: '1px solid #c6c6c6' }}>
        {approvals.map((approval) => (
          <button
            key={approval.payment_order_id}
            onClick={() => onApprovalClick(approval.payment_order_id)}
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
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <strong style={{ fontWeight: 600, fontSize: '16px' }}>
                  {approval.payee_name}
                </strong>
                <span
                  style={{
                    fontSize: '11px',
                    padding: '2px 6px',
                    background: '#fef3c7',
                    color: '#92400e',
                    border: '1px solid #fbbf24',
                    borderRadius: '2px',
                    fontWeight: 600,
                  }}
                >
                  PENDING
                </span>
              </div>
              <span style={{ fontSize: '14px', lineHeight: '20px', color: '#525252' }}>
                {formatMinor(approval.amount_minor, approval.currency_code)} • {approval.customer_payment_ref}
              </span>
              <span style={{ fontSize: '12px', lineHeight: '18px', color: '#525252' }}>
                From {approval.source_account_name}
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
      </div>
    </div>
  )
}
