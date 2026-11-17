export interface TransactionContext {
  transaction_id: string;
  merchant_name: string;
  amount: number;
  currency: string;
  transaction_date: string;
  card_last_four: string;
  status: string;
}

export interface StartResolveRequest {
  message_text: string;
  entry_context_type?: string;
  entry_context_ref?: string;
  status_context_shown?: boolean;
}

export interface SendMessageRequest {
  message_text: string;
}

export interface ResolveTurnEntry {
  role: string;
  content_text: string;
  occurred_at: string;
}

export interface ResolveTurnResponse {
  session_id: string;
  thread_id: string;
  state: string;
  ai_disclosure: boolean;
  human_path_shown: boolean;
  new_entries: ResolveTurnEntry[];
  case_ref?: string | null;
  case_id?: string | null;
  classification?: string | null;
}

export interface ResolveSessionView {
  session_id: string;
  thread_id: string;
  state: string;
  entries: ResolveTurnEntry[];
  case_ref?: string;
  classification?: string;
}

export interface HumanRequestResponse {
  session_id: string;
  thread_id: string;
  case_ref: string;
  case_id: string;
  owner_team_display?: string;
  expected_by_at?: string;
}

export interface EvidenceUploadResponse {
  evidence_id: string;
  display_label: string;
  evidence_type: string;
  state: string;
  received_at: string;
}

export interface ConfirmationRequest {
  sca_reference: string;
}
