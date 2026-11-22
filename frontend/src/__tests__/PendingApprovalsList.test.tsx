import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PendingApprovalsList } from '../components/payments/PendingApprovalsList'
import { PendingApproval } from '../features/payments/usePendingApprovals'

describe('PendingApprovalsList', () => {
  const mockApprovals: PendingApproval[] = [
    {
      payment_order_id: 'payment-1',
      customer_payment_ref: 'PAY-001',
      payee_name: 'ABC Suppliers Ltd',
      source_account_name: 'Business Current Account',
      amount_minor: 150000,
      currency_code: 'GBP',
      created_at: '2024-01-15T10:00:00Z',
    },
    {
      payment_order_id: 'payment-2',
      customer_payment_ref: 'PAY-002',
      payee_name: 'XYZ Services',
      source_account_name: 'Business Savings',
      amount_minor: 25000,
      currency_code: 'GBP',
      created_at: '2024-01-15T11:00:00Z',
    },
  ]

  it('should not render when approvals list is empty', () => {
    const { container } = render(
      <PendingApprovalsList approvals={[]} onApprovalClick={vi.fn()} />
    )

    expect(container.firstChild).toBeNull()
  })

  it('should render pending approvals header', () => {
    render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={vi.fn()}
      />
    )

    expect(
      screen.getByText('Payments awaiting approval')
    ).toBeInTheDocument()
    expect(
      screen.getByText(/These payments require a second approval/i)
    ).toBeInTheDocument()
  })

  it('should render all pending approvals', () => {
    render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={vi.fn()}
      />
    )

    expect(screen.getByText('ABC Suppliers Ltd')).toBeInTheDocument()
    expect(screen.getByText('XYZ Services')).toBeInTheDocument()
  })

  it('should display payment details correctly', () => {
    render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={vi.fn()}
      />
    )

    // Check formatted amount
    expect(screen.getByText(/£1,500.00/)).toBeInTheDocument()
    expect(screen.getByText(/£250.00/)).toBeInTheDocument()

    // Check payment references
    expect(screen.getByText(/PAY-001/)).toBeInTheDocument()
    expect(screen.getByText(/PAY-002/)).toBeInTheDocument()

    // Check source account names
    expect(screen.getByText(/From Business Current Account/)).toBeInTheDocument()
    expect(screen.getByText(/From Business Savings/)).toBeInTheDocument()
  })

  it('should display PENDING badge for each approval', () => {
    render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={vi.fn()}
      />
    )

    const pendingBadges = screen.getAllByText('PENDING')
    expect(pendingBadges).toHaveLength(mockApprovals.length)
  })

  it('should call onApprovalClick when approval is clicked', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={handleClick}
      />
    )

    const firstApproval = screen.getByText('ABC Suppliers Ltd').closest('button')
    expect(firstApproval).not.toBeNull()

    if (firstApproval) {
      await user.click(firstApproval)
      expect(handleClick).toHaveBeenCalledWith('payment-1')
    }
  })

  it('should call onApprovalClick with correct payment ID for each approval', async () => {
    const user = userEvent.setup()
    const handleClick = vi.fn()

    render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={handleClick}
      />
    )

    const firstApproval = screen.getByText('ABC Suppliers Ltd').closest('button')
    const secondApproval = screen.getByText('XYZ Services').closest('button')

    if (firstApproval && secondApproval) {
      await user.click(firstApproval)
      expect(handleClick).toHaveBeenCalledWith('payment-1')

      await user.click(secondApproval)
      expect(handleClick).toHaveBeenCalledWith('payment-2')
    }
  })

  it('should render chevron icon for each approval', () => {
    const { container } = render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={vi.fn()}
      />
    )

    const chevrons = container.querySelectorAll('svg[aria-hidden="true"]')
    expect(chevrons.length).toBe(mockApprovals.length)
  })

  it('should render approvals as buttons for accessibility', () => {
    render(
      <PendingApprovalsList
        approvals={mockApprovals}
        onApprovalClick={vi.fn()}
      />
    )

    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBe(mockApprovals.length)
  })
})
