/**
 * Money handling utilities
 * - Parse GBP strings to minor units (pence)
 * - Format minor units to display strings
 */

/**
 * Parse a GBP amount string to minor units (pence) - throws on error
 * Examples:
 *   "10.50" -> 1050
 *   "100" -> 10000
 *   "0.99" -> 99
 *
 * @param gbpString - GBP amount as string (e.g., "10.50")
 * @returns Amount in pence
 * @throws Error if invalid format
 */
export function parseGbpToMinor(gbpString: string): number {
  const cleaned = gbpString.replace(/[^\d.-]/g, '')
  const pounds = parseFloat(cleaned)
  if (isNaN(pounds)) {
    throw new Error(`Invalid GBP amount: ${gbpString}`)
  }
  return Math.round(pounds * 100)
}

/**
 * Safely parse a GBP amount string to minor units (pence)
 * Returns result object instead of throwing
 *
 * @param gbpString - GBP amount as string (e.g., "10.50")
 * @returns Result with value or error
 */
export function safeParseGbpToMinor(gbpString: string): {
  value: number | null
  error: string | null
} {
  try {
    const cleaned = gbpString.replace(/[^\d.-]/g, '')
    if (!cleaned || cleaned.trim() === '') {
      return { value: null, error: 'Amount is required' }
    }
    const pounds = parseFloat(cleaned)
    if (isNaN(pounds)) {
      return { value: null, error: 'Invalid amount format' }
    }
    return { value: Math.round(pounds * 100), error: null }
  } catch (e) {
    return { value: null, error: 'Invalid amount format' }
  }
}

/**
 * Format minor units (pence) to display string
 * Examples:
 *   1050 -> "£10.50"
 *   10000 -> "£100.00"
 *   99 -> "£0.99"
 *
 * @param minorUnits - Amount in pence
 * @param currency - Currency code (default: GBP)
 * @returns Formatted string with currency symbol
 */
export function formatMinor(
  minorUnits: number,
  currency: string = 'GBP'
): string {
  const pounds = minorUnits / 100
  
  // Use Intl.NumberFormat for proper formatting
  const formatter = new Intl.NumberFormat('en-GB', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })

  return formatter.format(pounds)
}

/**
 * Format minor units without currency symbol
 * Examples:
 *   1050 -> "10.50"
 *   10000 -> "100.00"
 *
 * @param minorUnits - Amount in pence
 * @returns Formatted numeric string
 */
export function formatMinorNumeric(minorUnits: number): string {
  const pounds = minorUnits / 100
  return pounds.toFixed(2)
}
