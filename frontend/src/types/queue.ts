/**
 * Queue item and refresh types
 */

export interface QueueItem {
  queue_item_id: string
  receivable_item_id: string
  customer_account_id: string
  customer_name: string
  queue_state: string
  is_non_standard: boolean
  non_standard_reason: string | null
  priority_rank: number
  priority_score: string
  open_amount: string
  currency_code: string
  days_past_due: number
  aging_bucket: string
  promise_indicator: boolean
  dispute_indicator: boolean
  entered_queue_at: string
  last_refreshed_at: string
}

export interface QueueGroup {
  queue_state: string
  count: number
  total_amount: string
}

export interface QueueListResponse {
  items: QueueItem[]
  total: number
  limit: number
  offset: number
  groups: QueueGroup[]
  data_freshness: string
}

export interface QueueRefreshRequest {
  scope: 'full' | 'customer'
  customer_id?: string
}

export interface RefreshRunResponse {
  run_id: string
  run_status: 'running' | 'completed' | 'failed'
  trigger_type: 'manual' | 'scheduled'
  started_at: string
  status_url: string
  completed_at?: string
  records_read?: number
  records_upserted?: number
  items_ranked?: number
  items_flagged_non_standard?: number
  error_summary?: string | null
}
