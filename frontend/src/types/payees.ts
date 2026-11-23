/**
 * Payee types
 */

export interface Payee {
  id: string;
  customer_profile_ref_id: string;
  payee_name: string;
  account_number: string;
  sort_code: string;
  cop_outcome: string | null;
  cop_matched_name: string | null;
  cop_checked_at: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PayeeCreateRequest {
  payee_name: string;
  account_number: string;
  sort_code: string;
}

export interface PayeeResponse {
  payee: Payee;
  cop_status: string;
}

export interface PayeeListResponse {
  payees: PayeeResponse[];
  total: number;
}
