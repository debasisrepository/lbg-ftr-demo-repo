import { describe, it, expect } from 'vitest';
import { cn, formatCurrency, formatDateTime, formatRelativeTime, getStatusBadgeColor, getRiskBadgeColor } from './utils';

describe('cn', () => {
  it('merges class names correctly', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
    expect(cn('foo', undefined, 'bar')).toBe('foo bar');
    const condition = false;
    expect(cn('foo', condition && 'bar', 'baz')).toBe('foo baz');
  });
});

describe('formatCurrency', () => {
  it('formats GBP currency correctly', () => {
    const result = formatCurrency(1234.56);
    expect(result).toContain('1,234.56');
    expect(result).toMatch(/£|GBP/);
  });

  it('handles zero', () => {
    const result = formatCurrency(0);
    expect(result).toContain('0.00');
  });

  it('handles negative values', () => {
    const result = formatCurrency(-100);
    expect(result).toContain('100');
  });
});

describe('formatDateTime', () => {
  it('formats ISO date string', () => {
    const result = formatDateTime('2024-01-15T10:30:00Z');
    // The function returns format like "15 Jan 2024, 10:30"
    expect(result).toMatch(/\d{1,2} \w{3} \d{4}/);
  });
});

describe('formatRelativeTime', () => {
  it('formats recent date as relative time', () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
    const result = formatRelativeTime(fiveMinutesAgo.toISOString());
    // Returns "5m ago" format
    expect(result).toMatch(/\d+m ago/);
  });

  it('formats just now for very recent times', () => {
    const now = new Date();
    const result = formatRelativeTime(now.toISOString());
    expect(result).toBe('Just now');
  });
});

describe('getStatusBadgeColor', () => {
  it('returns red for error statuses', () => {
    expect(getStatusBadgeColor('error')).toBe('red');
    expect(getStatusBadgeColor('failed')).toBe('red');
    expect(getStatusBadgeColor('critical')).toBe('red');
  });

  it('returns green for success statuses', () => {
    expect(getStatusBadgeColor('success')).toBe('green');
    expect(getStatusBadgeColor('completed')).toBe('green');
    expect(getStatusBadgeColor('resolved')).toBe('green');
  });

  it('returns blue for active statuses', () => {
    expect(getStatusBadgeColor('progress')).toBe('blue');
    expect(getStatusBadgeColor('active')).toBe('blue');
  });

  it('returns gray for unknown statuses', () => {
    expect(getStatusBadgeColor('unknown')).toBe('gray');
  });
});

describe('getRiskBadgeColor', () => {
  it('returns red for high risk', () => {
    expect(getRiskBadgeColor('high')).toBe('red');
    expect(getRiskBadgeColor('critical')).toBe('red');
    expect(getRiskBadgeColor('severe')).toBe('red');
  });

  it('returns magenta for medium risk', () => {
    expect(getRiskBadgeColor('medium')).toBe('magenta');
    expect(getRiskBadgeColor('moderate')).toBe('magenta');
  });

  it('returns teal for low risk', () => {
    expect(getRiskBadgeColor('low')).toBe('teal');
    expect(getRiskBadgeColor('minor')).toBe('teal');
  });

  it('returns gray for unknown risk', () => {
    expect(getRiskBadgeColor('unknown')).toBe('gray');
  });
});
