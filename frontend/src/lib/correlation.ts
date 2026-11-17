/**
 * Correlation ID utilities for distributed tracing
 */

/**
 * Generate a unique correlation ID for request tracing
 * @returns A unique correlation ID string
 */
export function generateCorrelationId(): string {
  // Use crypto.randomUUID if available (modern browsers)
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  
  // Fallback: timestamp-based approach with random component
  const timestamp = Date.now().toString(36);
  const randomPart = Math.random().toString(36).substring(2, 15);
  return `${timestamp}-${randomPart}`;
}
