export interface ScopeLink {
  link_type: 'invoice' | 'account_balance'
  invoice_id?: string
  linked_amount: string
}

export interface PromiseCreateRequest {
  customer_account_id: string
  promised_amount: string
  currency_code: string
  promised_date: string
  promise_scope_type: 'invoice' | 'account_balance' | 'partial'
  scope_links: ScopeLink[]
  source_interaction_id?: string
  note?: string
}

export interface PromiseScopeLinkResponse {
  link_id: string
  link_type: string
  invoice_id: string | null
  receivable_item_id: string | null
  linked_amount: string
}

export interface PromiseResponse {
  promise_id: string
  customer_account_id: string
  promised_amount: string
  currency_code: string
  promised_date: string
  promise_scope_type: string
  promise_status: string
  captured_by_user_id: string
  captured_at: string
  policy_evaluation_id: string | null
  scope_links: PromiseScopeLinkResponse[]
}

export interface PolicyFailureDetail {
  evaluation_result: 'deny'
  failed_conditions: Array<{
    rule_code: string
    condition_type: string
    failure_message: string
    parameters: Record<string, unknown>
  }>
}
