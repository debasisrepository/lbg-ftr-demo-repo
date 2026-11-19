/**
 * Shared TypeScript types matching backend schemas
 */

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in_seconds: number;
  session_id: number;
  step_up_required: boolean;
  available_step_up_methods: string[];
  active_profile_id?: number;
  user: {
    id: number;
    username: string;
    status: string;
  };
}

export interface User {
  id: number;
  username: string;
  status: string;
}

export interface Profile {
  profile_id: number;
  profile_type: string;
  display_name: string;
  business_name?: string;
  can_view_accounts: boolean;
  can_create_payee: boolean;
  can_approve_payment: boolean;
}

export interface ProfilesResponse {
  active_profile_id: number;
  profiles: Profile[];
}

export interface Account {
  account_id: number;
  account_type: string;
  account_name: string;
  masked_account_number: string;
  sort_code?: string;
  currency: string;
  current_balance_minor: number;
  available_balance_minor?: number;
  overdraft_available_minor?: number;
  available_credit_minor?: number;
  next_repayment_amount_minor?: number;
  next_repayment_due_date?: string;
  freshness_state: string;
  last_updated_at: string;
}

export interface DataGap {
  source_system: string;
  message: string;
  freshness_state: string;
}

export interface AccountsOverviewResponse {
  profile: Profile;
  accounts: Account[];
  data_gaps?: DataGap[];
}

export interface Payee {
  payee_id: number;
  display_name: string;
  sort_code: string;
  masked_account_number: string;
  nickname?: string;
  can_proceed: boolean;
  latest_cop_result?: string;
  latest_cop_checked_at?: string;
}

export interface PayeesResponse {
  payees: Payee[];
}

export interface CreatePayeeRequest {
  profile_id: number;
  display_name: string;
  nickname?: string;
  sort_code: string;
  account_number: string;
  payee_action_challenge_id: number;
  payee_action_assertion: string;
}

export interface CreatePayeeResponse {
  payee_id: number;
  display_name: string;
  sort_code: string;
  masked_account_number: string;
  cop_result: string;
  warning_message?: string;
  can_proceed: boolean;
  override_required: boolean;
}

export interface PaymentInstruction {
  id: number;
  profile_id: number;
  source_account_snapshot_id: number;
  payee_id: number;
  amount_minor: number;
  currency: string;
  reference_text?: string;
  instruction_state: string;
}

// Payment preparation types
export interface PaymentPrepareRequest {
  profile_id: number;
  source_account_id: number;
  payee_id: number;
  amount_minor: number;
  currency: string;
  reference?: string;
  client_idempotency_key?: string;
}

export interface PaymentPrepareResponse {
  payment_id: number;
  payment_state: string;
  amount_minor: number;
  currency: string;
  source_account_id: number;
  payee: {
    payee_id: number;
    display_name: string;
    sort_code: string;
    masked_account_number: string;
  };
  reference?: string;
  balance_check: {
    passed: boolean;
    available_balance_minor: number;
    detail?: string;
  };
  limit_check: {
    passed: boolean;
    configured_limit_minor: number;
    detail?: string;
  };
  fraud_decision: {
    decision: string;
    warning_message?: string;
    hold_reason?: string;
  };
  approval_required: boolean;
  approval_challenge?: {
    challenge_id: number;
    challenge_expires_at: string;
    dynamic_link_summary: {
      payee_name: string;
      amount_minor: number;
      currency: string;
    };
  };
}

// Payment approval types
export interface PaymentApproveRequest {
  challenge_id: number;
  method: string;
  passcode?: string;
  biometric_assertion?: string;
  device_id: string;
}

export interface PaymentApproveResponse {
  payment_id: number;
  status: string;
  amount_minor: number;
  currency: string;
  payee: {
    payee_id: number;
    display_name: string;
  };
  reference?: string;
  payment_reference: string;
  rail_reference?: string;
  expected_arrival_message?: string;
  duplicate_submission_blocked: boolean;
  next_actions: string[];
  failure_reason?: string;
}

// Payment status types
export interface PaymentStatusResponse {
  payment_id: number;
  status: string;
  amount_minor: number;
  currency: string;
  payee: {
    payee_id: number;
    display_name: string;
  };
  reference?: string;
  payment_reference: string;
  rail_reference?: string;
  expected_arrival_message?: string;
  duplicate_submission_blocked: boolean;
  status_last_updated_at: string;
  failure_reason?: string;
}

export interface ErrorResponse {
  detail: string;
}
