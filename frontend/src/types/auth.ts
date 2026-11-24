export interface User {
  id: string
  username: string
  display_name: string
  email: string
}

export interface RoleContext {
  role_code: string
  role_label: string
  allowed_widgets: string[]
  entitled_queue_states: string[]
  allowed_actions: string[]
  can_view_sensitive_fields: boolean
}

export interface LoginRequest {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  inactivity_timeout_seconds: number
  session_id: string
  user: User
  active_role_code: string
  available_roles: RoleContext[]
}

export interface SessionResponse {
  session_id: string
  user: User
  active_role_code: string
  available_roles: RoleContext[]
  issued_at: string
  expires_at: string
  seconds_until_inactivity_timeout: number
}

export interface LogoutResponse {
  session_id: string
  revoked_at: string
}
