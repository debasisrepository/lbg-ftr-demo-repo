export interface ApiError {
  detail: string
  status_code?: number
}

export interface HealthResponse {
  status: string
  service: string
  version: string
  time: string
}

export interface ReadinessCheck {
  name: string
  ok: boolean
  informational?: boolean
}

export interface ReadinessResponse {
  status: 'ready' | 'not_ready'
  checks: ReadinessCheck[]
}
