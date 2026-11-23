/**
 * API client for making authenticated requests to the backend.
 * Uses relative /api by default for same-origin deployment.
 */

// API base URL - defaults to relative /api for same-origin
const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Make an authenticated API request
 */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  // Get token from sessionStorage
  const token = sessionStorage.getItem('auth_token');
  
  // Prepare headers
  const headers = new Headers(options.headers);
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  
  // Make request
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
  
  // Handle errors
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      // Response is not JSON
    }
    
    throw new ApiError(
      `Request failed: ${response.status}`,
      response.status,
      detail
    );
  }
  
  // Handle empty responses
  if (response.status === 204 || response.headers.get('content-length') === '0') {
    return null as T;
  }
  
  // Parse JSON response
  return response.json() as Promise<T>;
}

/**
 * API client methods
 */
export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  
  patch: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),
  
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    }),
  
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

export default apiClient;
