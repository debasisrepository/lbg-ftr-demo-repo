import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import ScamReportPage from '../pages/ScamReportPage'

const mockNavigate = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: {
        payment_order_id: 'order-1',
        customer_payment_ref: 'PAY001',
        amount_minor: 25000,
        payee_name: 'Test Payee',
      },
    }),
  }
})

vi.mock('../features/support/useCreateScamClaim', () => ({
  useCreateScamClaim: () => ({
    createScamClaim: vi.fn(),
    loading: false,
    error: null,
  }),
}))

describe('ScamReportPage', () => {
  it('renders scam report form', () => {
    render(
      <BrowserRouter>
        <ScamReportPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/Tell us what happened/i)).toBeInTheDocument()
    expect(screen.getByText(/What type of scam was this/i)).toBeInTheDocument()
  })

  it('displays payment reference', () => {
    render(
      <BrowserRouter>
        <ScamReportPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/PAY001/i)).toBeInTheDocument()
  })

  it('displays payment details', () => {
    render(
      <BrowserRouter>
        <ScamReportPage />
      </BrowserRouter>
    )

    expect(screen.getByText(/£250.00 to Test Payee/i)).toBeInTheDocument()
  })

  it('shows scam reason options', () => {
    render(
      <BrowserRouter>
        <ScamReportPage />
      </BrowserRouter>
    )

    expect(
      screen.getByText(/I did not authorize this payment/i)
    ).toBeInTheDocument()
    expect(
      screen.getByText(/I believe this payment was fraudulent/i)
    ).toBeInTheDocument()
  })

  it('disables submit when no reason selected', () => {
    render(
      <BrowserRouter>
        <ScamReportPage />
      </BrowserRouter>
    )

    const submitButton = screen.getByRole('button', { name: /Report a scam/i })
    expect(submitButton).toBeDisabled()
  })

  it('allows text input in description', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <ScamReportPage />
      </BrowserRouter>
    )

    const descInput = screen.getByLabelText(/Tell us more/i)
    await user.type(descInput, 'Additional details')

    expect(descInput).toHaveValue('Additional details')
  })
})
