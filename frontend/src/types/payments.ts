/**
 * Payment types
 * 
 * CRITICAL: These types must exactly match backend/app/schemas/payments_schemas.py
 * Any drift will cause runtime errors and type mismatches.
 */

export interface PaymentIntent {
  id: string;
  customer_profile_ref_id: string;
  payee_id: string;
  amount_minor: number;
  currency: string;
  reference: string | null;
  internal_state: string;
  customer_visible_status: string;
  idempotency_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaymentStateTransition {
  id: string;
  payment_intent_id: string;
  from_state: string;
  to_state: string;
  trigger: string;
  metadata: Record<string, unknown> | null;
  transitioned_at: string;
}

export interface DynamicLinkApproval {
  id: string;
  payment_intent_id: string;
  ciam_transaction_reference: string;
  approval_outcome: string;
  approval_method: string | null;
  fingerprint_hash: string;
  approved_at: string | null;
  created_at: string;
}

export interface ScamCheckOutcome {
  id: string;
  payment_intent_id: string;
  check_reference: string;
  risk_score: number | null;
  risk_category: string;
  decision: string;
  warning_presented: boolean;
  customer_decision: string | null;
  decided_at: string | null;
  created_at: string;
}

export interface PaymentExecutionStatus {
  id: string;
  payment_intent_id: string;
  hub_submission_reference: string | null;
  hub_status: string;
  hub_status_timestamp: string | null;
  created_at: string;
  updated_at: string;
}

/**
 * CRITICAL FIX 2: PaymentCreateRequest now matches backend schema exactly
 * Backend: PaymentCreateRequest in payments_schemas.py
 */
export interface PaymentCreateRequest {
  source_account_id: string;
  payee_id: string;
  amount_minor: number;
  currency?: string; // defaults to "GBP" in backend
  payment_reference: string;
}

/**
 * Account summary in payment response
 * Backend: PaymentAccountSummary in payments_schemas.py
 */
export interface PaymentAccountSummary {
  account_id: string;
  display_name: string;
  masked_account_identifier: string;
}

/**
 * Payee summary in payment response
 * Backend: PaymentPayeeSummary in payments_schemas.py
 */
export interface PaymentPayeeSummary {
  payee_id: string;
  payee_name: string;
  masked_account_identifier: string;
}

/**
 * Warning details for payment response
 * Backend: PaymentWarning in payments_schemas.py
 */
export interface PaymentWarning {
  heading: string;
  body: string;
  allowed_actions: string[];
  policy_allows_continue: boolean;
}

/**
 * CRITICAL FIX 1: PaymentResponse now has all 20 fields from backend schema
 * Backend: PaymentResponse in payments_schemas.py
 * 
 * This is the unified response for E-07, E-08, E-09, E-10, E-11, E-12
 */
export interface PaymentResponse {
  payment_id: string;
  current_state: string;
  next_action: string;
  customer_visible_status: string | null;
  status_message: string;
  is_submitted: boolean;
  do_not_resubmit: boolean;
  payment_reference: string;
  amount_minor: number;
  currency: string;
  source_account: PaymentAccountSummary;
  payee: PaymentPayeeSummary;
  review_version: number;
  review_fingerprint: string;
  warning: PaymentWarning | null;
  hold_latest_decision_at: string | null;
  expected_arrival_time: string | null;
  payee_display_name: string;
  created_at: string;
  updated_at: string;
}

/**
 * Request schema for changing payment review (E-10)
 * Backend: PaymentChangeRequest in payments_schemas.py
 */
export interface PaymentChangeRequest {
  expected_review_version: number;
  source_account_id?: string;
  payee_id?: string;
  amount_minor?: number;
  payment_reference?: string;
}

/**
 * Step-up credential for dynamic-linking approval (E-11)
 * Backend: ApprovalCredential in payments_schemas.py
 */
export interface ApprovalCredential {
  method: string; // "passcode"
  passcode: string;
}

/**
 * Request schema for approving and submitting payment (E-11)
 * Backend: PaymentSubmitRequest in payments_schemas.py
 */
export interface PaymentSubmitRequest {
  review_version: number;
  review_fingerprint: string;
  approval: ApprovalCredential;
}

/**
 * Request schema for recording warning decision (E-12)
 * Backend: WarningDecisionRequest in payments_schemas.py
 */
export interface WarningDecisionRequest {
  review_version: number;
  decision: "stop" | "continue";
}

/**
 * CRITICAL FIX 3: PaymentListResponse now uses backend field names
 * Backend: PaymentListResponse in payments_schemas.py
 * Changed from: payments/limit/offset
 * Changed to: items/page/page_size (matches backend)
 */
export interface PaymentListResponse {
  items: PaymentResponse[];
  total: number;
  page: number;
  page_size: number;
}
