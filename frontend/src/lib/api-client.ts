/**
 * Centralized API client for all backend communication.
 * Base URL defaults to relative /api for same-origin proxying.
 */

const API_BASE = import.meta.env.VITE_API_URL ?? '/api'
const TOKEN_KEY = 'access_token'

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface RequestOptions extends RequestInit {
  skipAuth?: boolean
}

async function request<T>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth, ...fetchOptions } = options
  const url = `${API_BASE}${path}`
  
  const headers = new Headers(fetchOptions.headers)
  
  // Attach bearer token if not skipped
  if (!skipAuth) {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }
  
  // Set content-type for JSON bodies
  if (fetchOptions.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  
  const response = await fetch(url, {
    ...fetchOptions,
    headers,
  })
  
  // Handle 401: clear token and redirect to login
  if (response.status === 401) {
    localStorage.removeItem(TOKEN_KEY)
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
    throw new ApiError('Unauthorized', 401)
  }
  
  // Handle errors
  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`
    try {
      const errorData = await response.json()
      errorDetail = errorData.detail || errorDetail
    } catch {
      // Response was not JSON
    }
    throw new ApiError(errorDetail, response.status, errorDetail)
  }
  
  // Handle 204 No Content
  if (response.status === 204) {
    return null as T
  }
  
  // Parse JSON response
  try {
    return await response.json()
  } catch {
    return null as T
  }
}

export const apiClient = {
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'GET' })
  },
  
  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    })
  },
  
  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>(path, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    })
  },
  
  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>(path, { ...options, method: 'DELETE' })
  },
  
  // Auth helpers
  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },
  
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },
  
  clearToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  },
}
