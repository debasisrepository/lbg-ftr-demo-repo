/**
 * Client-side validation utilities
 * Mirrors server-side validation rules
 */

/**
 * Validate UK sort code format
 * @param sortCode - Sort code string (with or without hyphens)
 * @returns True if valid format
 */
export function isValidSortCode(sortCode: string): boolean {
  // Remove hyphens and spaces
  const cleaned = sortCode.replace(/[-\s]/g, '')
  // Must be exactly 6 digits
  return /^\d{6}$/.test(cleaned)
}

/**
 * Validate UK account number format
 * @param accountNumber - Account number string
 * @returns True if valid format
 */
export function isValidAccountNumber(accountNumber: string): boolean {
  // Remove spaces
  const cleaned = accountNumber.replace(/\s/g, '')
  // Must be 8 digits
  return /^\d{8}$/.test(cleaned)
}

/**
 * Validate sort code with error message
 * @param sortCode - Sort code string
 * @returns Validation result with error message if invalid
 */
export function validateSortCode(sortCode: string): {
  valid: boolean
  error?: string
} {
  if (!sortCode || sortCode.trim().length === 0) {
    return { valid: false, error: 'Sort code is required' }
  }

  if (!isValidSortCode(sortCode)) {
    return { valid: false, error: 'Sort code must be in format XX-XX-XX' }
  }

  return { valid: true }
}

/**
 * Validate account number with error message
 * @param accountNumber - Account number string
 * @returns Validation result with error message if invalid
 */
export function validateAccountNumber(accountNumber: string): {
  valid: boolean
  error?: string
} {
  if (!accountNumber || accountNumber.trim().length === 0) {
    return { valid: false, error: 'Account number is required' }
  }

  if (!isValidAccountNumber(accountNumber)) {
    return { valid: false, error: 'Account number must be 8 digits' }
  }

  return { valid: true }
}

/**
 * Validate payment amount
 * @param amountMinor - Amount in minor units (pence)
 * @returns Validation result with error message if invalid
 */
export function validatePaymentAmount(amountMinor: number): {
  valid: boolean
  error?: string
} {
  if (amountMinor <= 0) {
    return { valid: false, error: 'Amount must be greater than zero' }
  }

  // Max Faster Payment limit: £1,000,000
  const maxMinor = 100000000 // £1,000,000 in pence
  if (amountMinor > maxMinor) {
    return { valid: false, error: 'Amount exceeds maximum limit of £1,000,000' }
  }

  return { valid: true }
}

/**
 * Validate payment reference
 * @param reference - Payment reference string
 * @returns Validation result with error message if invalid
 */
export function validatePaymentReference(reference: string): {
  valid: boolean
  error?: string
} {
  if (!reference || reference.trim().length === 0) {
    return { valid: false, error: 'Payment reference is required' }
  }

  if (reference.length > 18) {
    return { valid: false, error: 'Payment reference must be 18 characters or less' }
  }

  // Only alphanumeric, spaces, and basic punctuation
  if (!/^[a-zA-Z0-9\s.,\-/()]+$/.test(reference)) {
    return {
      valid: false,
      error: 'Payment reference contains invalid characters',
    }
  }

  return { valid: true }
}

/**
 * Validate payee name
 * @param name - Payee name string
 * @returns Validation result with error message if invalid
 */
export function validatePayeeName(name: string): {
  valid: boolean
  error?: string
} {
  if (!name || name.trim().length === 0) {
    return { valid: false, error: 'Payee name is required' }
  }

  if (name.length < 2) {
    return { valid: false, error: 'Payee name must be at least 2 characters' }
  }

  if (name.length > 140) {
    return { valid: false, error: 'Payee name must be 140 characters or less' }
  }

  return { valid: true }
}

/**
 * Format sort code for display
 * @param sortCode - Sort code string
 * @returns Formatted sort code (XX-XX-XX)
 */
export function formatSortCode(sortCode: string): string {
  const cleaned = sortCode.replace(/[-\s]/g, '')
  if (cleaned.length !== 6) {
    return sortCode
  }
  return `${cleaned.slice(0, 2)}-${cleaned.slice(2, 4)}-${cleaned.slice(4, 6)}`
}

/**
 * Format account number for display
 * @param accountNumber - Account number string
 * @returns Formatted account number (XXXX XXXX)
 */
export function formatAccountNumber(accountNumber: string): string {
  const cleaned = accountNumber.replace(/\s/g, '')
  if (cleaned.length !== 8) {
    return accountNumber
  }
  return `${cleaned.slice(0, 4)} ${cleaned.slice(4, 8)}`
}
