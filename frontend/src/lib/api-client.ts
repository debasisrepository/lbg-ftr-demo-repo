/**
 * Centralized API client
 * - Same-origin `/api` integration
 * - Bearer token authentication
 * - Correlation ID tracking
 * - Error normalization
 */

import sharedConfig from '../../../shared_config.json'

// The only place `/api` is written on the frontend
const API_BASE = import.meta.env.VITE_API_URL ?? '/api'
const API_VERSION = `/${sharedConfig.api_version}`

export interface ApiError {
  message: string
  status: number
  detail?: string
}

export class ApiClientError extends Error {
  status: number
  detail?: string

  constructor(message: string, status: number, detail?: string) {
    super(message)
    this.name = 'ApiClientError'
    this.status = status
    this.detail = detail
  }
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
}

/**
 * Generate a correlation ID for request tracking
 */
function generateCorrelationId(): string {
  return `web-${Date.now()}-${Math.random().toString(36).substring(2, 15)}`
}

/**
 * Central request handler
 */
async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, ...fetchOptions } = options
  const token = localStorage.getItem(sharedConfig.auth_storage_key)

  const headers = new Headers(fetchOptions.headers)
  
  // Add auth header unless skipped
  if (!skipAuth && token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  // Add correlation ID
  headers.set('X-Correlation-ID', generateCorrelationId())

  // Set content type for JSON bodies
  if (fetchOptions.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const url = `${API_BASE}${API_VERSION}${path}`

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
    })

    // Handle 401 - only clear token and redirect if this was an authenticated request
    if (response.status === 401 && !skipAuth) {
      localStorage.removeItem(sharedConfig.auth_storage_key)
      window.location.href = '/login'
      throw new ApiClientError('Unauthorized', 401)
    }

    // Handle non-OK responses
    if (!response.ok) {
      let errorDetail = `Request failed with status ${response.status}`
      try {
        const errorData = await response.json()
        errorDetail = errorData.detail || errorData.message || errorDetail
      } catch {
        // If response is not JSON, use status text
        errorDetail = response.statusText || errorDetail
      }
      throw new ApiClientError(errorDetail, response.status, errorDetail)
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return null as T
    }

    // Parse JSON response
    return (await response.json()) as T
  } catch (error) {
    if (error instanceof ApiClientError) {
      throw error
    }
    // Network error or other fetch failure
    throw new ApiClientError(
      error instanceof Error ? error.message : 'Network request failed',
      0
    )
  }
}

/**
 * GET request
 */
export async function get<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>(path, { ...options, method: 'GET' })
}

/**
 * POST request
 */
export async function post<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  return request<T>(path, {
    ...options,
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * PUT request
 */
export async function put<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  return request<T>(path, {
    ...options,
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * PATCH request
 */
export async function patch<T>(
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  return request<T>(path, {
    ...options,
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  })
}

/**
 * DELETE request
 */
export async function del<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>(path, { ...options, method: 'DELETE' })
}

export const apiClient = {
  get,
  post,
  put,
  patch,
  delete: del,
}
