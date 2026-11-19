/**
 * Unit tests for money utilities
 */

import { describe, it, expect } from 'vitest'
import { parseGbpToMinor, formatMinor, formatMinorNumeric } from '../lib/money'

describe('money utilities', () => {
  describe('parseGbpToMinor', () => {
    it('should parse GBP string to pence', () => {
      expect(parseGbpToMinor('10.50')).toBe(1050)
      expect(parseGbpToMinor('100')).toBe(10000)
      expect(parseGbpToMinor('0.99')).toBe(99)
      expect(parseGbpToMinor('1000.00')).toBe(100000)
    })

    it('should handle strings with currency symbol', () => {
      expect(parseGbpToMinor('£10.50')).toBe(1050)
      expect(parseGbpToMinor('£100')).toBe(10000)
    })

    it('should throw on invalid input', () => {
      expect(() => parseGbpToMinor('invalid')).toThrow()
      expect(() => parseGbpToMinor('')).toThrow()
    })
  })

  describe('formatMinor', () => {
    it('should format pence to GBP string', () => {
      expect(formatMinor(1050)).toBe('£10.50')
      expect(formatMinor(10000)).toBe('£100.00')
      expect(formatMinor(99)).toBe('£0.99')
    })

    it('should handle zero', () => {
      expect(formatMinor(0)).toBe('£0.00')
    })

    it('should handle negative amounts', () => {
      expect(formatMinor(-1050)).toBe('-£10.50')
    })
  })

  describe('formatMinorNumeric', () => {
    it('should format pence to numeric string', () => {
      expect(formatMinorNumeric(1050)).toBe('10.50')
      expect(formatMinorNumeric(10000)).toBe('100.00')
      expect(formatMinorNumeric(99)).toBe('0.99')
    })
  })
})
