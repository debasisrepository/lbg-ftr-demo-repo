/**
 * Unit tests for validators
 */

import { describe, it, expect } from 'vitest'
import {
  isValidSortCode,
  isValidAccountNumber,
  validatePaymentAmount,
  validatePaymentReference,
  validatePayeeName,
  formatSortCode,
  formatAccountNumber,
} from '../lib/validators'

describe('validators', () => {
  describe('isValidSortCode', () => {
    it('should validate correct sort codes', () => {
      expect(isValidSortCode('123456')).toBe(true)
      expect(isValidSortCode('12-34-56')).toBe(true)
      expect(isValidSortCode('12 34 56')).toBe(true)
    })

    it('should reject invalid sort codes', () => {
      expect(isValidSortCode('12345')).toBe(false)
      expect(isValidSortCode('1234567')).toBe(false)
      expect(isValidSortCode('12-34-5')).toBe(false)
      expect(isValidSortCode('abc123')).toBe(false)
    })
  })

  describe('isValidAccountNumber', () => {
    it('should validate correct account numbers', () => {
      expect(isValidAccountNumber('12345678')).toBe(true)
      expect(isValidAccountNumber('1234 5678')).toBe(true)
    })

    it('should reject invalid account numbers', () => {
      expect(isValidAccountNumber('1234567')).toBe(false)
      expect(isValidAccountNumber('123456789')).toBe(false)
      expect(isValidAccountNumber('abcd5678')).toBe(false)
    })
  })

  describe('validatePaymentAmount', () => {
    it('should accept valid amounts', () => {
      expect(validatePaymentAmount(100).valid).toBe(true)
      expect(validatePaymentAmount(1000000).valid).toBe(true)
    })

    it('should reject zero and negative amounts', () => {
      expect(validatePaymentAmount(0).valid).toBe(false)
      expect(validatePaymentAmount(-100).valid).toBe(false)
    })

    it('should reject amounts over limit', () => {
      const result = validatePaymentAmount(100000001)
      expect(result.valid).toBe(false)
      expect(result.error).toContain('exceeds maximum')
    })
  })

  describe('validatePaymentReference', () => {
    it('should accept valid references', () => {
      expect(validatePaymentReference('Invoice 123').valid).toBe(true)
      expect(validatePaymentReference('Rent-Nov-2024').valid).toBe(true)
    })

    it('should reject empty references', () => {
      expect(validatePaymentReference('').valid).toBe(false)
      expect(validatePaymentReference('   ').valid).toBe(false)
    })

    it('should reject references over 18 chars', () => {
      const result = validatePaymentReference('This is a very long reference')
      expect(result.valid).toBe(false)
      expect(result.error).toContain('18 characters')
    })

    it('should reject invalid characters', () => {
      expect(validatePaymentReference('Test@123').valid).toBe(false)
      expect(validatePaymentReference('Test#123').valid).toBe(false)
    })
  })

  describe('validatePayeeName', () => {
    it('should accept valid names', () => {
      expect(validatePayeeName('John Doe').valid).toBe(true)
      expect(validatePayeeName('ABC Ltd').valid).toBe(true)
    })

    it('should reject empty names', () => {
      expect(validatePayeeName('').valid).toBe(false)
      expect(validatePayeeName('   ').valid).toBe(false)
    })

    it('should reject names too short', () => {
      expect(validatePayeeName('J').valid).toBe(false)
    })

    it('should reject names too long', () => {
      const longName = 'A'.repeat(141)
      const result = validatePayeeName(longName)
      expect(result.valid).toBe(false)
    })
  })

  describe('formatSortCode', () => {
    it('should format sort code with hyphens', () => {
      expect(formatSortCode('123456')).toBe('12-34-56')
    })

    it('should leave invalid sort codes unchanged', () => {
      expect(formatSortCode('12345')).toBe('12345')
    })
  })

  describe('formatAccountNumber', () => {
    it('should format account number with space', () => {
      expect(formatAccountNumber('12345678')).toBe('1234 5678')
    })

    it('should leave invalid account numbers unchanged', () => {
      expect(formatAccountNumber('1234567')).toBe('1234567')
    })
  })
})
