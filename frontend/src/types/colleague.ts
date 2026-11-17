// Colleague types matching backend schemas

export interface ColleagueCaseListItem {
  case_id: string;
  case_ref: string;
  status_code: string;
  classification_code?: string;
  owner_team_display?: string;
  owner_colleague_display?: string;
  expected_by_at?: string;
  last_update_at: string;
}

export interface ColleagueCaseListResponse {
  items: ColleagueCaseListItem[];
  total: number;
}

export interface HandoffPackResponse {
  case_id: string;
  case_ref: string;
  status_code: string;
  problem_statement: string;
  classification_code?: string;
  route_reason?: string;
  arrival_source?: string;
  expected_by_at?: string;
  owner_team_display?: string;
  owner_colleague_display?: string;
  handoff_summary_text?: string;
  vulnerability_flag?: boolean;
  copilot_note?: string;
  customer_display_name?: string;
  brand?: string;
  opened_at?: string;
}

export interface TranscriptEntryResponse {
  entry_id: string;
  role: string;
  content_text: string;
  visibility_scope: 'customer_and_colleague' | 'colleague_only';
  occurred_at: string;
}

export interface ThreadResponse {
  entries: TranscriptEntryResponse[];
  total: number;
}

export interface ColleagueReplyRequest {
  content_text: string;
  visibility_scope: 'customer_and_colleague' | 'colleague_only';
}

export interface EvidenceRequestRequest {
  display_label: string;
  evidence_type?: string;
}

export interface PickupRequest {
  colleague_user_id: string;
}
