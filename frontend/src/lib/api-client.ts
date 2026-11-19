/**
 * Centralized API client with Bearer token attachment and 401 handling
 */

import sharedConfig from '../../../shared_config.json';

// API base defaults to /api for same-origin requests
const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

/**
 * Base request function with authentication and error handling
 */
async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem(sharedConfig.auth.tokenStorageKey);
  const headers = new Headers(options.headers);

  // Attach Bearer token if available
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  // Set Content-Type for JSON bodies
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const url = `${API_BASE}/v1${path}`;
  const response = await fetch(url, { ...options, headers });

  // Handle 401 Unauthorized - clear token and redirect to login
  if (response.status === 401) {
    localStorage.removeItem(sharedConfig.auth.tokenStorageKey);
    window.location.href = '/login';
    throw new Error('Unauthorized');
  }

  // Handle other error responses
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = 'Request failed';
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.detail || errorMessage;
    } catch {
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json() as Promise<T>;
}

/**
 * HTTP GET request
 */
export async function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' });
}

/**
 * HTTP POST request
 */
export async function post<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * HTTP PUT request
 */
export async function put<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * HTTP PATCH request
 */
export async function patch<T>(path: string, body?: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PATCH',
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * HTTP DELETE request
 */
export async function del<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'DELETE' });
}

export const apiClient = {
  get,
  post,
  put,
  patch,
  delete: del,
};

export default apiClient;
