import { useState, useEffect, useCallback } from 'react';
import { apiClient, ApiError } from '../lib/api-client';
import type { StatusSnapshot } from '../types/api';

export interface StatusPollState {
  status: StatusSnapshot | null;
  loading: boolean;
  error: string | null;
}

/**
 * Hook that polls GET /status every max_age_seconds
 * Respects cache_version and only updates when version changes
 */
export function useStatusPoll(maxAgeSeconds: number = 60): StatusPollState {
  const [status, setStatus] = useState<StatusSnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastCacheVersion, setLastCacheVersion] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const result = await apiClient.get<StatusSnapshot>('/status');
      
      // Only update if cache version changed
      if (!lastCacheVersion || result.cache_version !== lastCacheVersion) {
        setStatus(result);
        setLastCacheVersion(result.cache_version);
      }
      
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else if (err instanceof Error) {
        setError(err.message);
      } else {
        setError('Failed to fetch status');
      }
    } finally {
      setLoading(false);
    }
  }, [lastCacheVersion]);

  useEffect(() => {
    // Initial fetch
    fetchStatus();

    // Set up polling interval
    const intervalId = setInterval(fetchStatus, maxAgeSeconds * 1000);

    // Cleanup
    return () => clearInterval(intervalId);
  }, [fetchStatus, maxAgeSeconds]);

  return {
    status,
    loading,
    error,
  };
}
