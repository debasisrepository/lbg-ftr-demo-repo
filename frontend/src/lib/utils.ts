import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge class names with Tailwind conflict resolution
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

/**
 * Format currency with locale awareness
 */
export function formatCurrency(amount: number, currency = 'GBP'): string {
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency,
  }).format(amount);
}

/**
 * Format ISO datetime to readable string
 */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format ISO date to readable date string (no time)
 */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-GB', {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format relative time (e.g., "3 hours ago")
 */
export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  
  const years = Math.floor(months / 12);
  return `${years}y ago`;
}

/**
 * Get Carbon Tag kind for status badges
 */
export function getStatusBadgeColor(status: string): 'red' | 'magenta' | 'purple' | 'blue' | 'cyan' | 'teal' | 'green' | 'gray' | 'cool-gray' | 'warm-gray' | 'high-contrast' {
  const normalized = status.toLowerCase();
  
  if (normalized.includes('fail') || normalized.includes('error') || normalized.includes('critical')) {
    return 'red';
  }
  if (normalized.includes('warn') || normalized.includes('pending')) {
    return 'magenta';
  }
  if (normalized.includes('progress') || normalized.includes('active')) {
    return 'blue';
  }
  if (normalized.includes('success') || normalized.includes('complete') || normalized.includes('resolved')) {
    return 'green';
  }
  
  return 'gray';
}

/**
 * Get Carbon Tag kind for risk badges
 */
export function getRiskBadgeColor(risk: string): 'red' | 'magenta' | 'purple' | 'blue' | 'cyan' | 'teal' | 'green' | 'gray' | 'cool-gray' | 'warm-gray' | 'high-contrast' {
  const normalized = risk.toLowerCase();
  
  if (normalized.includes('high') || normalized.includes('critical') || normalized.includes('severe')) {
    return 'red';
  }
  if (normalized.includes('medium') || normalized.includes('moderate')) {
    return 'magenta';
  }
  if (normalized.includes('low') || normalized.includes('minor')) {
    return 'teal';
  }
  
  return 'gray';
}
