export type SectionStatus = 'available' | 'unavailable' | 'masked'

export interface Section<T> {
  status: SectionStatus
  reason?: string
  as_of?: string
  data?: T
}

export interface CustomerProfile {
  customer_id: string
  customer_name: string
  sap_customer_ref: string
  regional_business_unit: string
  credit_status_indicator: string | null
  master_data_source: string
}

export interface CustomerAccount {
  customer_account_id: string
  sap_account_ref: string
  company_code: string
  currency_code: string
  account_status: string
  risk_segment: string
  portfolio_ref: string
  collector_owner_user_id: string | null
  open_balance: string
}

export interface Invoice {
  invoice_id: string
  sap_invoice_ref: string
  invoice_number: string
  document_date: string
  due_date: string
  invoice_amount: string
  open_amount: string
  currency_code: string
  invoice_status: string
  days_past_due?: number
}

export interface ReceivableItem {
  receivable_item_id: string
  invoice_id: string
  sap_open_item_ref: string
  aging_bucket: string
  days_past_due: number
  open_amount: string
  currency_code: string
  dispute_indicator: boolean
  deduction_indicator: boolean
}

export interface UnappliedCash {
  unapplied_cash_id: string
  sap_cash_item_ref: string
  bank_or_lockbox_reference: string
  receipt_date: string
  unapplied_amount: string
  currency_code: string
  classification_status: string
  aging_days: number
}

export interface Promise {
  promise_id: string
  customer_account_id: string
  promised_amount: string
  currency_code: string
  promised_date: string
  promise_scope_type: string
  promise_status: string
  captured_by_user_id: string
  captured_at: string
  breach_detected_at?: string | null
}

export interface SourceInteraction {
  interaction_id: string
  interaction_type: string
  interaction_direction: string
  interaction_channel: string
  occurred_at: string
  recorded_by_user_id: string
  summary_text: string
}

export interface Customer360Response {
  customer_id: string
  generated_at: string
  data_freshness: string
  profile: Section<CustomerProfile>
  accounts: Section<CustomerAccount[]>
  invoices: Section<Invoice[]>
  receivable_items: Section<ReceivableItem[]>
  unapplied_cash: Section<UnappliedCash[]>
  promises: Section<Promise[]>
  source_interactions: Section<SourceInteraction[]>
}
