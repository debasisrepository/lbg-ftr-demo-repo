// Case types matching backend schemas

export interface CaseListItem {
  id: string;
  case_ref: string;
  status: string;
  classification?: string;
  owner_team_display?: string;
  owner_colleague_display?: string;
  last_update_at: string;
  expected_by_at?: string;
}

export interface CaseListResponse {
  items: CaseListItem[];
  total: number;
}

export interface CaseDetailResponse {
  id: string;
  case_ref: string;
  customer_user_id: string;
  status: string;
  problem_statement: string;
  classification?: string;
  owner_team_display?: string;
  owner_colleague_display?: string;
  route_reason?: string;
  expected_by_at?: string;
  last_update_at: string;
  created_at: string;
}

export interface CaseConfirmation {
  case_id: string;
  case_ref: string;
  owner_team_display?: string;
  expected_by_at?: string;
  problem_summary?: string;
  what_we_sent?: {
    description: boolean;
    transaction: boolean;
    evidence: boolean;
    transcript: boolean;
  };
}
