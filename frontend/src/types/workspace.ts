/**
 * Workspace and landing page types
 */

export interface LandingWidget {
  widget_code: string
  widget_label: string
  widget_data: Record<string, unknown>
}

export interface LandingResponse {
  active_role_code: string
  active_role_label: string
  available_roles: Array<{
    role_code: string
    role_label: string
  }>
  allowed_actions: string[]
  widgets: LandingWidget[]
  data_freshness: string
  generated_at: string
}

export interface ActiveRoleRequest {
  role_code: string
}

export interface ActiveRoleResponse {
  previous_role_code: string
  active_role_code: string
  allowed_actions: string[]
  switched_at: string
}
