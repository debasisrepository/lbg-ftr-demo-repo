/**
 * Lifeline cache - stores the last successful lifeline response in localStorage
 * for offline fallback when the backend is unavailable
 */

const CACHE_KEY = 'clearpath_lifeline_cache';

export interface LifelineCache {
  guidance_items: Array<{
    id: string;
    incident_reference: string;
    guidance_category: string;
    guidance_title: string;
    guidance_body: string;
    published_at: string;
  }>;
  protective_actions: string[];
  fallback_channels: Array<{
    channel_type: string;
    label: string;
    contact_detail: string | null;
    availability_text: string | null;
  }>;
  cache_version: string;
  cache_age_seconds: number;
  generated_at: string;
  withdrawn_cache_versions: string[];
}

/**
 * Get the cached lifeline data
 */
export function getLifelineCache(): LifelineCache | null {
  try {
    const cached = localStorage.getItem(CACHE_KEY);
    if (!cached) return null;
    
    const data = JSON.parse(cached);
    
    // Check if cache_version is withdrawn
    if (data.withdrawn_cache_versions?.includes(data.cache_version)) {
      // Clear withdrawn cache
      localStorage.removeItem(CACHE_KEY);
      return null;
    }
    
    return data;
  } catch {
    return null;
  }
}

/**
 * Set the lifeline cache with a new response
 */
export function setLifelineCache(data: LifelineCache): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    // Ignore cache write failures (quota exceeded, etc)
  }
}

/**
 * Calculate the age of the cached data in seconds
 */
export function getCacheAgeSeconds(cache: LifelineCache): number {
  const generatedAt = new Date(cache.generated_at);
  const now = new Date();
  const ageFromGenerated = Math.floor((now.getTime() - generatedAt.getTime()) / 1000);
  
  // Add the cache_age_seconds from the response (time since newest item was published)
  return cache.cache_age_seconds + ageFromGenerated;
}

/**
 * Format cache age for display (e.g. "5 minutes old")
 */
export function formatCacheAge(ageSeconds: number): string {
  if (ageSeconds < 60) {
    return `${ageSeconds} seconds old`;
  } else if (ageSeconds < 3600) {
    const minutes = Math.floor(ageSeconds / 60);
    return `${minutes} minute${minutes !== 1 ? 's' : ''} old`;
  } else if (ageSeconds < 86400) {
    const hours = Math.floor(ageSeconds / 3600);
    return `${hours} hour${hours !== 1 ? 's' : ''} old`;
  } else {
    const days = Math.floor(ageSeconds / 86400);
    return `${days} day${days !== 1 ? 's' : ''} old`;
  }
}
