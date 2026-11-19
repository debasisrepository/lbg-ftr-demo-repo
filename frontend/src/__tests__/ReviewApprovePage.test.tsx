import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import ReviewApprovePage from '../pages/ReviewApprovePage'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../features/payments/PaymentFlowProvider', () => ({
  usePaymentFlow: () => ({
    preparedPayment: {
      payment_order_id: 'order-1',
      customer_payment_ref: 'PAY001',
      payment_reference: 'Test',
      amount_minor: 25000,
      currency_code: 'GBP',
      source_account_name: 'Current Account',
      payee_name: 'K Evans Lettings',
      limit_checks_passed: true,
      risk_decision: 'allow',
      requires_approval: true,
      dynamic_link_digest: 'abc123',
    },
    riskFriction: null,
    setRiskFriction: vi.fn(),
    paymentOrderId: 'order-1',
    transitionTo: vi.fn(),
  }),
}))

vi.mock('../features/payments/useApprovePayment', () => ({
  useApprovePayment: () => ({
    approvePayment: vi.fn(),
    loading: false,
    error: null,
  }),
}))

vi.mock('../features/payments/useSubmitPayment', () => ({
  useSubmitPayment: () => ({
    submitPayment: vi.fn(),
    loading: false,
    error: null,
  }),
}))

vi.mock('../features/payments/useRiskResponse', () => ({
  useRiskResponse: () => ({
    respondToRisk: vi.fn(),
    loading: false,
    error: null,
  }),
}))

describe('ReviewApprovePage', () => {
  it('renders payment review details', () => {
    render(
      <BrowserRouter>
        <ReviewApprovePage />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { name: /Approve payment/i })).toBeInTheDocument()
    expect(screen.getByText(/Current Account/i)).toBeInTheDocument()
    // Use getAllByText for text that appears multiple times, then assert on the array
    const payeeElements = screen.getAllByText(/K Evans Lettings/i)
    expect(payeeElements.length).toBeGreaterThan(0)
    // Amount appears multiple times - just verify one exists
    const amountElements = screen.getAllByText(/£250.00/i)
    expect(amountElements.length).toBeGreaterThan(0)
  })

  it('displays Face ID approval option', () => {
    render(
      <BrowserRouter>
        <ReviewApprovePage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Approve with Face ID/i)).toBeInTheDocument()
  })

  it('shows cancel button', () => {
    render(
      <BrowserRouter>
        <ReviewApprovePage />
      </BrowserRouter>
    )

    expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument()
  })
})
