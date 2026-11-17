import { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiError } from '../lib/api-client';

export interface ResourceState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  serviceUnavailable: boolean;
  refetch: () => Promise<void>;
}

/**
 * Generic hook for fetching API resources with loading/error/unavailable states
 */
export function useResource<T>(
  fetcher: () => Promise<T>,
  deps: React.DependencyList = []
): ResourceState<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [serviceUnavailable, setServiceUnavailable] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setServiceUnavailable(false);

    try {
      const result = await fetcher();
      setData(result);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 503) {
          setServiceUnavailable(true);
          setError('Service temporarily unavailable. Please try again later.');
        } else {
          setError(err.detail);
        }
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('An unexpected error occurred');
      }
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    serviceUnavailable,
    refetch: fetchData,
  };
}

/**
 * Fetch cases list
 */
export function useCases(includeClosed: boolean = true) {
  return useResource(
    () => apiClient.get<{ items: import('../types/api').CaseSummary[] }>(`/cases?include_closed=${includeClosed}`),
    [includeClosed]
  );
}

/**
 * Fetch service status
 */
export function useStatus() {
  return useResource(
    () => apiClient.get<import('../types/api').StatusSnapshot>('/status'),
    []
  );
}

/**
 * Fetch notifications
 */
export function useNotifications() {
  return useResource(
    () => apiClient.get<{ items: import('../types/api').NotificationItem[] }>('/notifications'),
    []
  );
}
