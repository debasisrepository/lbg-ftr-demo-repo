/**
 * Account and transaction types
 */

export interface AccountReadModel {
  id: string;
  customer_profile_ref_id: string;
  account_system_reference: string;
  account_type: string;
  display_name: string;
  masked_account_identifier: string;
  balance_amount_minor: number | null;
  balance_currency: string;
  balance_as_of_timestamp: string | null;
  freshness_status: string;
  provenance: string;
  created_at: string;
  updated_at: string;
}

export interface AccountSummary {
  account: AccountReadModel;
  freshness_indicator: string;
  display_balance: string | null;
}

export interface AccountsOverviewResponse {
  accounts: AccountSummary[];
  overall_freshness: string;
  degraded_capability: boolean;
}
