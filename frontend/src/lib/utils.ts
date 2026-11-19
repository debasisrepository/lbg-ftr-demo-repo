import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merges CSS class names using clsx and tailwind-merge
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format amount in minor units to currency string
 * @param amountMinor Amount in minor units (e.g., 25000 = £250.00)
 * @param currency Currency code (default: GBP)
 */
export function formatCurrency(amountMinor: number, currency = 'GBP'): string {
  const amount = amountMinor / 100;
  return new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency,
  }).format(amount);
}

/**
 * Format ISO datetime string to readable format
 */
export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString('en-GB', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
}

/**
 * Format ISO datetime to relative time (e.g., "3 hours ago")
 */
export function formatRelativeTime(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

/**
 * Get Carbon badge color for status codes
 */
export function getStatusBadgeColor(status: string): 'green' | 'yellow' | 'red' | 'gray' {
  const statusLower = status.toLowerCase();
  if (statusLower === 'sent' || statusLower === 'active' || statusLower === 'verified') {
    return 'green';
  }
  if (statusLower === 'pending' || statusLower === 'delayed') {
    return 'yellow';
  }
  if (statusLower === 'failed' || statusLower === 'locked' || statusLower === 'expired') {
    return 'red';
  }
  return 'gray';
}

/**
 * Get Carbon badge color for risk/fraud decision codes
 */
export function getRiskBadgeColor(code: string): 'green' | 'yellow' | 'red' | 'gray' {
  const codeLower = code.toLowerCase();
  if (codeLower === 'allow') {
    return 'green';
  }
  if (codeLower === 'warn' || codeLower === 'step_up') {
    return 'yellow';
  }
  if (codeLower === 'hold') {
    return 'red';
  }
  return 'gray';
}
