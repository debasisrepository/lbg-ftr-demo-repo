import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueueTable } from '../components/queue/QueueTable'
import userEvent from '@testing-library/user-event'
import type { QueueItem } from '../types/queue'

describe('QueueTable', () => {
  const mockItems: QueueItem[] = [
    {
      queue_item_id: '1',
      receivable_item_id: 'r1',
      customer_account_id: 'c1',
      customer_name: 'ABC Corp',
      queue_state: 'active',
      is_non_standard: false,
      non_standard_reason: null,
      priority_rank: 1,
      priority_score: '1500.00',
      open_amount: '15000.00',
      currency_code: 'USD',
      days_past_due: 60,
      aging_bucket: '61-90',
      promise_indicator: false,
      dispute_indicator: false,
      entered_queue_at: '2026-11-01T00:00:00Z',
      last_refreshed_at: '2026-11-24T07:42:00Z',
    },
    {
      queue_item_id: '2',
      receivable_item_id: 'r2',
      customer_account_id: 'c2',
      customer_name: 'XYZ Ltd',
      queue_state: 'active',
      is_non_standard: true,
      non_standard_reason: 'disputed',
      priority_rank: 2,
      priority_score: '1200.00',
      open_amount: '12000.00',
      currency_code: 'USD',
      days_past_due: 45,
      aging_bucket: '31-60',
      promise_indicator: false,
      dispute_indicator: true,
      entered_queue_at: '2026-11-10T00:00:00Z',
      last_refreshed_at: '2026-11-24T07:42:00Z',
    },
  ]

  it('renders queue items in a table', () => {
    const onOpenCustomer = vi.fn()
    render(<QueueTable items={mockItems} onOpenCustomer={onOpenCustomer} />)

    expect(screen.getByRole('table')).toBeInTheDocument()
    expect(screen.getByText('ABC Corp')).toBeInTheDocument()
    expect(screen.getByText('XYZ Ltd')).toBeInTheDocument()
  })

  it('displays correct status pills', () => {
    const onOpenCustomer = vi.fn()
    render(<QueueTable items={mockItems} onOpenCustomer={onOpenCustomer} />)

    expect(screen.getByText('Ready for action')).toBeInTheDocument()
    expect(screen.getByText(/Non-standard: disputed/i)).toBeInTheDocument()
  })

  it('highlights non-standard rows', () => {
    const onOpenCustomer = vi.fn()
    const { container } = render(<QueueTable items={mockItems} onOpenCustomer={onOpenCustomer} />)

    const rows = container.querySelectorAll('tbody tr')
    expect(rows[0]).not.toHaveClass('bg-[#FDF5EC]')
    expect(rows[1]).toHaveClass('bg-[#FDF5EC]')
  })

  it('calls onOpenCustomer when button is clicked', async () => {
    const onOpenCustomer = vi.fn()
    const user = userEvent.setup()
    
    render(<QueueTable items={mockItems} onOpenCustomer={onOpenCustomer} />)

    const buttons = screen.getAllByRole('button', { name: /Open Customer 360/i })
    await user.click(buttons[0]!)

    expect(onOpenCustomer).toHaveBeenCalledWith('c1')
  })

  it('formats currency amounts correctly', () => {
    const onOpenCustomer = vi.fn()
    render(<QueueTable items={mockItems} onOpenCustomer={onOpenCustomer} />)

    expect(screen.getByText('$15,000.00')).toBeInTheDocument()
    expect(screen.getByText('$12,000.00')).toBeInTheDocument()
  })
})
