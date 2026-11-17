import sharedConfig from '../../../shared_config.json';

// The only place `/api` is written on the frontend.
const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

interface RequestOptions {
  method?: string;
  headers?: HeadersInit;
  body?: unknown;
  skipAuthRedirect?: boolean;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public statusText: string
  ) {
    super(detail || statusText);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const token = localStorage.getItem(sharedConfig.auth.storage_key);
  const headers = new Headers(options.headers);

  if (token) {
    headers.set('Authorization', `${sharedConfig.auth.token_type} ${token}`);
  }

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const url = `${API_BASE}${path}`;
  const fetchOptions: RequestInit = {
    method: options.method,
    headers,
  };

  if (options.body && typeof options.body === 'object') {
    fetchOptions.body = JSON.stringify(options.body);
  }

  const response = await fetch(url, fetchOptions);

  if (response.status === 401) {
    // Don't auto-redirect if skipAuthRedirect is true (e.g., during login)
    if (!options.skipAuthRedirect) {
      localStorage.removeItem(sharedConfig.auth.storage_key);
      window.location.href = '/login';
    }
    
    let detail = 'Unauthorized';
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      // If response is not JSON, use default
    }
    throw new ApiError(401, detail, response.statusText);
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errorData = await response.json();
      detail = errorData.detail || detail;
    } catch {
      // If response is not JSON, use statusText
    }
    throw new ApiError(response.status, detail, response.statusText);
  }

  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: 'GET' }),
  post: <T>(path: string, body?: unknown, skipAuthRedirect = false) => 
    request<T>(path, { method: 'POST', body, skipAuthRedirect }),
  put: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PUT', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};
