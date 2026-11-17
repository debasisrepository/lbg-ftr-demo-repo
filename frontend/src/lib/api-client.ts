import sharedConfig from '../../../shared_config.json';

// The only place /api is written on the frontend
const baseUrl = import.meta.env.VITE_API_URL ?? '/api';

/**
 * API error with status and detail message
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

/**
 * Make an authenticated API request
 */
async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = localStorage.getItem(sharedConfig.auth.storage_key);
  const headers = new Headers(options.headers);
  
  if (token) {
    headers.set('Authorization', sharedConfig.auth.header_format.replace('{token}', token));
  }
  
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  
  // Build URL: /api + /v1 + <path>
  const url = `${baseUrl}${sharedConfig.api_base_path}${path}`;
  
  const response = await fetch(url, {
    ...options,
    headers,
  });
  
  // Handle 401 - clear token and redirect to login
  if (response.status === 401) {
    localStorage.removeItem(sharedConfig.auth.storage_key);
    window.location.href = '/login';
    throw new ApiError(401, 'Unauthorized');
  }
  
  // Handle non-2xx responses
  if (!response.ok) {
    let detail = 'Request failed';
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      detail = await response.text() || detail;
    }
    throw new ApiError(response.status, detail);
  }
  
  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }
  
  return response.json() as Promise<T>;
}

/**
 * API client methods
 */
export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  put: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  patch: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: 'PATCH',
      body: data ? JSON.stringify(data) : undefined,
    }),
  
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
