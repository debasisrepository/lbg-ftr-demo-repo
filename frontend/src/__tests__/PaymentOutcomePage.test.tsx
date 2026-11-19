import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import PaymentOutcomePage from '../pages/PaymentOutcomePage'

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
    paymentOrderId: 'order-1',
    resetFlow: vi.fn(),
  }),
}))

vi.mock('../features/payments/usePaymentStatus', () => ({
  usePaymentStatus: () => ({
    status: {
      payment_order_id: 'order-1',
      customer_payment_ref: 'PAY001',
      payment_reference: 'Test',
      amount_minor: 25000,
      currency_code: 'GBP',
      payee_name: 'K Evans Lettings',
      normalized_status: 'sent',
      current_internal_state: 'completed',
      expected_arrival_text: 'Usually arrives within minutes',
      created_at: '2026-11-19T10:00:00Z',
      updated_at: '2026-11-19T10:00:00Z',
    },
    loading: false,
    error: null,
    refetch: vi.fn(),
  }),
}))

describe('PaymentOutcomePage', () => {
  it('renders sent payment status', () => {
    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    )

    // Query by heading which should be unique
    expect(screen.getByRole('heading', { name: /Payment sent/i })).toBeInTheDocument()
    expect(screen.getByText(/£250.00/i)).toBeInTheDocument()
    expect(screen.getByText(/K Evans Lettings/i)).toBeInTheDocument()
  })

  it('displays payment reference', () => {
    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    )

    expect(screen.getByText(/PAY001/i)).toBeInTheDocument()
  })

  it('shows back to accounts button', () => {
    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    )

    expect(
      screen.getByRole('button', { name: /Back to accounts/i })
    ).toBeInTheDocument()
  })

  it('shows make another payment button', () => {
    render(
      <BrowserRouter>
        <PaymentOutcomePage />
      </BrowserRouter>
    )

    expect(
      screen.getByRole('button', { name: /Make another payment/i })
    ).toBeInTheDocument()
  })
})
