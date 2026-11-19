/**
 * Central type definitions
 * Mirrors backend API schemas
 */

// Auth types
export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: User
}

export interface User {
  customer_id: string
  username: string
  profile_id?: string
  auth_level: string
}

// Customer types
export interface Customer {
  customer_id: string
  external_identity_ref: string
  customer_type: string
  first_name?: string
  status: string
  created_at: string
  updated_at: string
}

export interface Profile {
  profile_id: string
  customer_id: string
  profile_type: string
  external_profile_ref: string
  display_name?: string
  status: string
  created_at: string
  updated_at: string
}

export interface Entitlement {
  entitlement_id: string
  profile_id: string
  entitlement_code: string
  capability_type: string
  can_view_accounts: boolean
  can_manage_payees: boolean
  can_initiate_payments: boolean
  effective_from?: string
  effective_to?: string
  created_at: string
  updated_at: string
}

// Account types
export interface BankAccount {
  bank_account_id: string
  external_account_ref: string
  account_type: string
  account_name?: string
  sort_code_masked: string
  account_number_masked: string
  currency_code: string
  account_holder_name?: string
  current_balance_minor: number
  available_balance_minor: number
  overdraft_limit_minor: number
  freshness_at: string
  source_status: string
  created_at: string
  updated_at: string
}

export interface LoanSnapshot {
  loan_snapshot_id: string
  profile_id: string
  external_loan_ref: string
  loan_name?: string
  outstanding_balance_minor: number
  next_repayment_minor?: number
  next_repayment_date?: string
  currency_code: string
  freshness_at: string
  source_status: string
  created_at: string
  updated_at: string
}

// Payee types
export interface Payee {
  payee_id: string
  customer_id: string
  profile_id: string
  external_payee_ref?: string
  payee_name: string
  sort_code: string
  account_number_masked: string
  payee_type: string
  is_saved: boolean
  status: string
  created_at: string
  updated_at: string
}

export interface CopCheck {
  cop_check_id: string
  payee_id: string
  request_reference: string
  check_trigger: string
  checked_name: string
  checked_sort_code: string
  outcome: string
  suggested_name?: string
  policy_treatment: string
  customer_acknowledged_at?: string
  created_at: string
  updated_at: string
}

// Payment types
export interface PaymentOrder {
  payment_order_id: string
  customer_id: string
  profile_id: string
  source_account_id: string
  payee_id: string
  cop_check_id?: string
  idempotency_key: string
  customer_payment_ref?: string
  payment_reference: string
  amount_minor: number
  currency_code: string
  payment_type: string
  internal_state: string
  normalized_state: string
  created_at: string
  updated_at: string
}

export interface PaymentLimit {
  payment_limit_id: string
  profile_id: string
  bank_account_id?: string
  limit_type: string
  payment_type: string
  amount_limit_minor: number
  currency_code: string
  effective_from?: string
  effective_to?: string
  created_at: string
  updated_at: string
}

// Session types
export interface Session {
  session_id: string
  customer_id: string
  device_id?: string
  active_profile_id?: string
  auth_level: string
  started_at: string
  last_activity_at: string
  expires_at: string
  inactivity_timeout_seconds: number
}

// Error types
export interface ApiError {
  detail: string
  status_code?: number
}

// Pagination types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}
