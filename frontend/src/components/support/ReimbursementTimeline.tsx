/**
 * Reimbursement Timeline Component
 * Displays expected timeline for scam reimbursement
 * Based on UK regulatory requirements (CMP-RES-05)
 */

interface ReimbursementTimelineProps {
  claimType: string
}

export function ReimbursementTimeline({ claimType }: ReimbursementTimelineProps) {
  // Timeline based on claim type
  const isAuthorizedPushPayment = [
    'romance_scam',
    'investment_scam',
    'impersonation_scam',
    'purchase_scam',
  ].includes(claimType)

  const timelineSteps = isAuthorizedPushPayment
    ? [
        { day: '0', label: 'Report received', description: 'We\'ve logged your claim' },
        { day: '1', label: 'Initial contact', description: 'We\'ll contact you within 24 hours' },
        { day: '15', label: 'Decision', description: 'We\'ll make a decision on your claim' },
        { day: '15', label: 'Reimbursement', description: 'If approved, funds returned within 15 business days' },
      ]
    : [
        { day: '0', label: 'Report received', description: 'We\'ve logged your claim' },
        { day: '1', label: 'Initial contact', description: 'We\'ll contact you within 24 hours' },
        { day: '1-2', label: 'Investigation', description: 'We\'ll investigate with you' },
        { day: '15', label: 'Reimbursement', description: 'If unauthorized, refund within 1 business day' },
      ]

  return (
    <div style={{ marginTop: '24px' }}>
      <h3 style={{ fontSize: '20px', lineHeight: '28px', fontWeight: 600, marginBottom: '12px' }}>
        What happens next
      </h3>
      <p style={{ fontSize: '14px', lineHeight: '20px', color: '#525252', marginBottom: '16px' }}>
        {isAuthorizedPushPayment
          ? 'Authorized push payment scams are assessed under the voluntary industry code.'
          : 'Unauthorized payments are typically refunded quickly once verified.'}
      </p>

      <div style={{ position: 'relative', paddingLeft: '32px' }}>
        {/* Timeline line */}
        <div
          style={{
            position: 'absolute',
            left: '7px',
            top: '8px',
            bottom: '8px',
            width: '2px',
            background: '#c6c6c6',
          }}
          aria-hidden="true"
        />

        {timelineSteps.map((step, index) => (
          <div key={index} style={{ position: 'relative', paddingBottom: '20px' }}>
            {/* Timeline dot */}
            <div
              style={{
                position: 'absolute',
                left: '-28px',
                top: '4px',
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                background: index === 0 ? '#161616' : '#ffffff',
                border: '2px solid #161616',
              }}
              aria-hidden="true"
            />

            <div>
              <div style={{ fontSize: '12px', color: '#525252', fontWeight: 600, marginBottom: '2px' }}>
                Day {step.day}
              </div>
              <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: '2px' }}>
                {step.label}
              </div>
              <div style={{ fontSize: '14px', color: '#525252' }}>
                {step.description}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          marginTop: '16px',
          padding: '12px',
          background: '#f3f4f6',
          border: '1px solid #c6c6c6',
          fontSize: '14px',
          lineHeight: '20px',
        }}
      >
        <p style={{ margin: 0, fontWeight: 600, marginBottom: '4px' }}>
          Important information
        </p>
        <ul style={{ margin: 0, paddingLeft: '20px' }}>
          <li>We may need additional information from you</li>
          <li>Timelines may vary based on case complexity</li>
          <li>You'll receive updates at each stage</li>
        </ul>
      </div>
    </div>
  )
}
