import { CopCheckOut } from '../../features/payees/usePayees'

interface CopOutcomePanelProps {
  copCheck: CopCheckOut
  onAcknowledge?: () => void
}

export function CopOutcomePanel({ copCheck, onAcknowledge }: CopOutcomePanelProps) {
  const { outcome, policy_treatment, suggested_name } = copCheck

  // Determine banner styling and messaging based on outcome
  const getBannerConfig = () => {
    switch (outcome) {
      case 'match':
        return {
          title: 'Name matches',
          message: 'We checked the name against the account. The details match.',
          borderColor: '#161616',
          showAcknowledge: false,
        }
      case 'partial_match':
        return {
          title: "Warning: the name doesn't match",
          message: `The name you entered is close to, but not the same as, the name on this account${
            suggested_name ? ` (${suggested_name})` : ''
          }. Check the details before you continue. Paying the wrong account could mean you can't get your money back.`,
          borderColor: '#c62828',
          showAcknowledge: policy_treatment === 'warn',
        }
      case 'mismatch':
        return {
          title: "Warning: the name doesn't match",
          message: `The name you entered is close to, but not the same as, the name on this account${
            suggested_name ? ` (${suggested_name})` : ''
          }. Check the details before you continue. Paying the wrong account could mean you can't get your money back.`,
          borderColor: '#c62828',
          showAcknowledge: policy_treatment === 'warn',
        }
      case 'unavailable':
        return {
          title: "We couldn't check this payee",
          message:
            "We can't confirm the name on this account right now, so we haven't added the payee. Try again in a few minutes, or choose a saved payee.",
          borderColor: '#c62828',
          showAcknowledge: false,
        }
      default:
        return {
          title: 'Confirmation of Payee check completed',
          message: 'Please review the details before continuing.',
          borderColor: '#161616',
          showAcknowledge: false,
        }
    }
  }

  const config = getBannerConfig()

  return (
    <div>
      <div
        role={outcome === 'unavailable' || outcome === 'mismatch' || outcome === 'partial_match' ? 'alert' : undefined}
        style={{
          border: '1px solid #8d8d8d',
          borderLeft: `4px solid ${config.borderColor}`,
          background: '#f4f4f4',
          padding: '12px 16px',
          marginBottom: '16px',
          fontSize: '14px',
          lineHeight: '20px',
        }}
      >
        <strong
          style={{
            display: 'block',
            fontSize: '16px',
            lineHeight: '24px',
            marginBottom: '4px',
          }}
        >
          Confirmation of Payee: {config.title}
        </strong>
        {config.message}
      </div>
      {config.showAcknowledge && onAcknowledge && (
        <button
          type="button"
          onClick={onAcknowledge}
          style={{
            display: 'block',
            width: '100%',
            minHeight: '52px',
            border: '2px solid #161616',
            fontSize: '16px',
            fontWeight: 600,
            fontFamily: 'inherit',
            padding: '0 16px',
            background: '#161616',
            color: '#fff',
            cursor: 'pointer',
          }}
        >
          I understand, continue
        </button>
      )}
    </div>
  )
}
