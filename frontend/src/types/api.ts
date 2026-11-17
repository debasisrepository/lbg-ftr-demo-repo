/**
 * API type definitions mirroring backend schemas
 */

export interface UserSummary {
  id: string;
  username: string;
  email: string | null;
  display_name: string | null;
  scope: string;
  customer_party_id: string | null;
  brand: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
  channel?: string;
}

export interface LoginResponse extends TokenResponse {
  inactivity_timeout_seconds: number;
  session_id: string;
  user: UserSummary;
}

export type RefreshResponse = TokenResponse;

export interface MeResponse {
  user: UserSummary;
  session_id: string;
  expires_at: string;
  last_activity_at: string;
}

// Case Management Types

export interface OwnerView {
  owner_team_code: string;
  owner_semantic_label: string;
  owner_type: 'named_person' | 'team' | 'role';
  owner_display_name: string;
  effective_from: string;
}

export interface ExpectedByView {
  commitment_state: string;
  expected_by_at: string | null;
  customer_explanatory_text: string;
  confidence_basis: string;
  effective_from: string;
}

export interface CaseSummary {
  case_reference: string;
  issue_type: string;
  issue_title: string;
  current_lifecycle_state: string;
  status_code: string;
  status_label: string;
  latest_meaningful_update_text: string;
  latest_meaningful_update_at: string | null;
  owner: OwnerView;
  expected_by: ExpectedByView;
  opened_at: string;
  closed_at: string | null;
  outcome_summary: string | null;
}

export interface CaseDetail extends CaseSummary {
  customer_party_id: string;
  brand: string;
  classification_source: string;
  issue_summary: string;
  origin_channel: string;
  status_summary_text: string;
  next_step_text: string | null;
  outage_impact_banner_text: string | null;
  continuity_state: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface CaseCreateRequest {
  issue_type: string;
  issue_summary: string;
  issue_title?: string;
  origin_channel: string;
  brand?: string;
}

export interface CaseCreateResponse {
  outcome: 'created' | 'surfaced' | 'not_eligible';
  case?: CaseDetail;
  classification_source?: string;
  anchor_reference?: string;
  redirect_journey_code?: string | null;
  redirect_message?: string | null;
  continuity_available?: boolean;
}

export interface NotificationItem {
  id: string;
  case_id: string;
  case_reference: string | null;
  notification_type: string;
  safe_preview_text: string;
  deep_link_target: string;
  opened_at: string | null;
  created_at: string;
}

// Case History Types

export interface HistoryEvent {
  id: string;
  sequence_number: number;
  event_type: string;
  event_timestamp: string;
  summary_text: string;
  customer_visible_flag: boolean;
  actor_type: string | null;
  actor_reference: string | null;
  basis_type: string | null;
  basis_reference: string | null;
  lifecycle_from: string | null;
  lifecycle_to: string | null;
}

// Protected Actions Types

export interface ProtectedAction {
  action_id: string;
  action_type: string;
  action_domain: string;
  request_status: 'pending_sca' | 'released' | 'not_executed';
  sca_outcome: 'not_invoked' | 'success' | 'failed' | 'abandoned';
  sca_invoked_at: string | null;
  sca_completed_at: string | null;
  management_api_reference: string | null;
  fallback_guidance_text: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface StartProtectedActionRequest {
  action_type: string;
  action_domain: string;
  action_payload: Record<string, unknown>;
}

export interface StartProtectedActionResponse {
  action_id: string;
  sca_challenge_reference: string;
}

export interface ReportScaOutcomeRequest {
  sca_outcome: 'success' | 'failed' | 'abandoned';
  sca_verification_token: string;
}

// Service Status Types

export interface StatusPublication {
  headline_text: string;
  summary_text: string;
  affected_journeys: string[];
  published_at: string;
}

export interface StatusIncident {
  incident_reference: string;
  incident_state: string;
  affected_service_code: string;
  customer_impact_summary: string;
  started_at: string;
  resolved_at: string | null;
  publications: StatusPublication[];
}

export interface StatusSnapshot {
  status_state: 'operational' | 'disruption';
  incidents: StatusIncident[];
  lifeline_available: boolean;
  generated_at: string;
  cache_version: string | null;
  max_age_seconds: number;
}
