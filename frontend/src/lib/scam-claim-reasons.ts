/**
 * Scam claim reasons
 * Mirrors ref_code group 'scam_claim_reason' from backend
 */

export interface ScamClaimReason {
  code: string
  label: string
}

export const SCAM_CLAIM_REASONS: ScamClaimReason[] = [
  { code: 'unauthorized_payment', label: 'I did not authorize this payment' },
  { code: 'suspected_fraud', label: 'I believe this payment was fraudulent' },
  { code: 'romance_scam', label: 'Romance or dating scam' },
  { code: 'investment_scam', label: 'Investment or get-rich-quick scam' },
  { code: 'impersonation_scam', label: 'Someone impersonated a business or official' },
  { code: 'purchase_scam', label: 'I paid for something that was never delivered' },
  { code: 'other', label: 'Other scam or suspicious payment' },
]
