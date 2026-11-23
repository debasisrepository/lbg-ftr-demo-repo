import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LoanCard } from '../components/accounts/LoanCard';

describe('LoanCard', () => {
  it('renders loan account with all details available', () => {
    const loan = {
      account_id: 'loan-001',
      account_type: 'loan' as const,
      display_name: 'Personal Loan',
      masked_account_identifier: '****3456',
      balance: {
        availability_state: 'current' as const,
        amount_minor: 1500000,
        currency: 'GBP',
        display_text: '£15,000.00',
      },
      as_of_timestamp: '2026-11-23T10:30:00Z',
      freshness_status: 'within_target' as const,
      freshness_text: 'Updated 1 minute ago',
      item_state: 'available' as const,
      payment_source_eligible: true,
      loan_details: {
        outstanding_balance_minor: 1500000,
        next_repayment_date: '2026-12-08T00:00:00Z',
        next_repayment_amount_minor: 50000,
        remaining_term_months: 30,
      },
    };

    render(<LoanCard account={loan} />);

    expect(screen.getByRole('heading', { name: /personal loan/i })).toBeInTheDocument();
    expect(screen.getByText(/loan ending \*\*\*\*3456/i)).toBeInTheDocument();
    expect(screen.getByText(/£15,000.00/)).toBeInTheDocument();
    expect(screen.getByText(/next repayment/i)).toBeInTheDocument();
    expect(screen.getByText(/£500.00/)).toBeInTheDocument();
    expect(screen.getByText(/30 months/i)).toBeInTheDocument();
  });

  it('renders loan with unavailable servicing gracefully', () => {
    const loan = {
      account_id: 'loan-002',
      account_type: 'loan' as const,
      display_name: 'Personal Loan',
      masked_account_identifier: '****3456',
      balance: {
        availability_state: 'unavailable' as const,
        amount_minor: null,
        currency: null,
        display_text: 'Balance unavailable',
      },
      as_of_timestamp: '2026-11-23T10:30:00Z',
      freshness_status: 'unknown' as const,
      freshness_text: 'Not current',
      item_state: 'partial' as const,
      payment_source_eligible: false,
      loan_details: {
        outstanding_balance_minor: null,
        next_repayment_date: null,
        next_repayment_amount_minor: null,
        remaining_term_months: null,
      },
    };

    render(<LoanCard account={loan} />);

    expect(screen.getByText(/balance unavailable/i)).toBeInTheDocument();
    expect(screen.getByText(/loan details temporarily unavailable/i)).toBeInTheDocument();
    expect(screen.queryByText(/£0/)).not.toBeInTheDocument();
  });

  it('renders loan with stale balance and shows freshness indicator', () => {
    const loan = {
      account_id: 'loan-003',
      account_type: 'loan' as const,
      display_name: 'Personal Loan',
      masked_account_identifier: '****3456',
      balance: {
        availability_state: 'stale' as const,
        amount_minor: 1500000,
        currency: 'GBP',
        display_text: '£15,000.00 (may be out of date)',
      },
      as_of_timestamp: '2026-11-23T08:00:00Z',
      freshness_status: 'breached' as const,
      freshness_text: 'Last updated at 08:00',
      item_state: 'available' as const,
      payment_source_eligible: false,
      loan_details: {
        outstanding_balance_minor: 1500000,
        next_repayment_date: '2026-12-08T00:00:00Z',
        next_repayment_amount_minor: 50000,
        remaining_term_months: 30,
      },
    };

    render(<LoanCard account={loan} />);

    expect(screen.getByText(/may be out of date/i)).toBeInTheDocument();
    expect(screen.getByText(/last updated at 08:00/i)).toBeInTheDocument();
  });

  it('renders loan with no next repayment (fully paid)', () => {
    const loan = {
      account_id: 'loan-004',
      account_type: 'loan' as const,
      display_name: 'Personal Loan',
      masked_account_identifier: '****3456',
      balance: {
        availability_state: 'current' as const,
        amount_minor: 0,
        currency: 'GBP',
        display_text: '£0.00',
      },
      as_of_timestamp: '2026-11-23T10:30:00Z',
      freshness_status: 'within_target' as const,
      freshness_text: 'Updated 1 minute ago',
      item_state: 'available' as const,
      payment_source_eligible: true,
      loan_details: {
        outstanding_balance_minor: 0,
        next_repayment_date: null,
        next_repayment_amount_minor: null,
        remaining_term_months: 0,
      },
    };

    render(<LoanCard account={loan} />);

    expect(screen.getByText(/£0.00/)).toBeInTheDocument();
    expect(screen.getByText(/loan fully repaid/i)).toBeInTheDocument();
    expect(screen.queryByText(/next repayment/i)).not.toBeInTheDocument();
  });
});
