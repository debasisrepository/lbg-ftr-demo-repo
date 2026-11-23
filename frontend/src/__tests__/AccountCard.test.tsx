import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { AccountCard } from '../components/accounts/AccountCard';

describe('AccountCard', () => {
  it('renders current account with balance and freshness', () => {
    const account = {
      account_id: 'acc-001',
      account_type: 'current',
      display_name: 'Main Current Account',
      masked_account_identifier: '****1234',
      balance: {
        availability_state: 'current' as const,
        amount_minor: 124836,
        currency: 'GBP',
        display_text: '£1,248.36',
      },
      as_of_timestamp: '2026-11-22T10:30:00Z',
      freshness_status: 'within_target' as const,
      freshness_text: 'Updated 2 minutes ago',
      item_state: 'available' as const,
      payment_source_eligible: true,
    };

    render(<AccountCard account={account} />);

    expect(screen.getByRole('heading', { name: /main current account/i })).toBeInTheDocument();
    expect(screen.getByText(/account ending \*\*\*\*1234/i)).toBeInTheDocument();
    expect(screen.getByText(/£1,248.36/)).toBeInTheDocument();
    expect(screen.getByText(/^current$/i)).toBeInTheDocument();
    expect(screen.getByText(/updated 2 minutes ago/i)).toBeInTheDocument();
  });

  it('renders stale account with appropriate badge', () => {
    const account = {
      account_id: 'acc-002',
      account_type: 'current',
      display_name: 'Joint Account',
      masked_account_identifier: '****9012',
      balance: {
        availability_state: 'stale' as const,
        amount_minor: 124836,
        currency: 'GBP',
        display_text: '£1,248.36',
      },
      as_of_timestamp: '2026-11-22T08:12:00Z',
      freshness_status: 'breached' as const,
      freshness_text: 'Last updated today at 08:12',
      item_state: 'available' as const,
      payment_source_eligible: false,
    };

    render(<AccountCard account={account} />);

    // Check that "may be out of date" appears (both in badge and text)
    const matches = screen.getAllByText(/may be out of date/i);
    expect(matches.length).toBeGreaterThan(0);
    
    // Check the specific balance text
    expect(screen.getByText(/balance may be out of date.*last updated/i)).toBeInTheDocument();
  });

  it('renders unavailable balance without showing zero', () => {
    const account = {
      account_id: 'acc-003',
      account_type: 'savings',
      display_name: 'Everyday Savings',
      masked_account_identifier: '****4417',
      balance: {
        availability_state: 'unavailable' as const,
        amount_minor: null,
        currency: null,
        display_text: 'Balance unavailable',
      },
      as_of_timestamp: '2026-11-22T10:30:00Z',
      freshness_status: 'unknown' as const,
      freshness_text: 'Not current',
      item_state: 'available' as const,
      payment_source_eligible: false,
    };

    render(<AccountCard account={account} />);

    expect(screen.getByText(/balance unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/£0/)).not.toBeInTheDocument();
    expect(screen.getAllByText(/unavailable/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/not current.*could not confirm/i)).toBeInTheDocument();
  });

  it('renders partial account with appropriate messaging', () => {
    const account = {
      account_id: 'acc-004',
      account_type: 'savings',
      display_name: 'Everyday Savings',
      masked_account_identifier: '****4417',
      balance: {
        availability_state: 'unavailable' as const,
        amount_minor: null,
        currency: null,
        display_text: 'Balance unavailable',
      },
      as_of_timestamp: '2026-11-22T10:30:00Z',
      freshness_status: 'unknown' as const,
      freshness_text: 'Not current',
      item_state: 'partial' as const,
      payment_source_eligible: false,
    };

    render(<AccountCard account={account} />);

    expect(screen.getByText(/partly available/i)).toBeInTheDocument();
    expect(screen.getByText(/cannot be used to pay from right now/i)).toBeInTheDocument();
  });

  it('never shows missing balance as £0.00', () => {
    const accountUnavailable = {
      account_id: 'acc-005',
      account_type: 'savings',
      display_name: 'Savings Account',
      masked_account_identifier: '****5555',
      balance: {
        availability_state: 'unavailable' as const,
        amount_minor: null,
        currency: null,
        display_text: 'Balance unavailable',
      },
      as_of_timestamp: '2026-11-22T10:30:00Z',
      freshness_status: 'unknown' as const,
      freshness_text: 'Not current',
      item_state: 'available' as const,
      payment_source_eligible: false,
    };

    const { rerender } = render(<AccountCard account={accountUnavailable} />);

    expect(screen.getByText(/balance unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/£0\.00/)).not.toBeInTheDocument();

    const accountUnknown = {
      ...accountUnavailable,
      account_id: 'acc-006',
      balance: {
        ...accountUnavailable.balance,
        availability_state: 'unknown' as const,
        display_text: 'Balance cannot be shown',
      },
    };

    rerender(<AccountCard account={accountUnknown} />);

    expect(screen.getByText(/balance cannot be shown/i)).toBeInTheDocument();
    expect(screen.queryByText(/£0\.00/)).not.toBeInTheDocument();
  });

  it('renders account type and masked identifier correctly', () => {
    const account = {
      account_id: 'acc-007',
      account_type: 'savings',
      display_name: 'Instant Saver',
      masked_account_identifier: '****5678',
      balance: {
        availability_state: 'current' as const,
        amount_minor: 350000,
        currency: 'GBP',
        display_text: '£3,500.00',
      },
      as_of_timestamp: '2026-11-22T10:30:00Z',
      freshness_status: 'within_target' as const,
      freshness_text: 'Updated 1 minute ago',
      item_state: 'available' as const,
      payment_source_eligible: true,
    };

    render(<AccountCard account={account} />);

    expect(screen.getByRole('heading', { name: /instant saver/i })).toBeInTheDocument();
    expect(screen.getByText(/account ending \*\*\*\*5678/i)).toBeInTheDocument();
  });
});
