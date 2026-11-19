import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import userEvent from '@testing-library/user-event'
import EnterPaymentPage from '../pages/EnterPaymentPage'
import { PaymentFlowProvider } from '../features/payments/PaymentFlowProvider'

const mockNavigate = vi.fn()
const mockSetPreparedPayment = vi.fn()

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: {
        payee_id: 'payee-1',
        payee_name: 'Test Payee',
        sort_code: '04-00-04',
        account_number_masked: '****3746',
      },
    }),
  }
})

vi.mock('../features/accounts/useAccountsOverview', () => ({
  useAccountsOverview: () => ({
    data: {
      accounts: [
        {
          bank_account_id: 'acc-1',
          account_name: 'Current Account',
          account_type: 'current',
          available_balance_minor: 124836,
          sort_code_masked: '20-45-77',
          account_number_masked: '****9842',
        },
      ],
      loans: [],
      profile_id: 'test-profile',
      profile_display_name: 'Test User',
    },
    loading: false,
    error: null,
  }),
}))

vi.mock('../features/payments/usePreparePayment', () => ({
  usePreparePayment: () => ({
    preparePayment: vi.fn().mockResolvedValue({
      data: {
        payment_order_id: 'order-1',
        customer_payment_ref: 'PAY001',
        payment_reference: 'Test',
        amount_minor: 5000,
        currency_code: 'GBP',
        source_account_name: 'Current Account',
        payee_name: 'Test Payee',
        limit_checks_passed: true,
        risk_decision: 'allow',
        requires_approval: true,
        dynamic_link_digest: 'abc123',
      },
    }),
    loading: false,
    error: null,
  }),
}))

vi.mock('../features/payments/PaymentFlowProvider', async () => {
  const actual = await vi.importActual('../features/payments/PaymentFlowProvider')
  return {
    ...actual,
    usePaymentFlow: () => ({
      setPreparedPayment: mockSetPreparedPayment,
    }),
  }
})

describe('EnterPaymentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders payment entry form', () => {
    render(
      <BrowserRouter>
        <PaymentFlowProvider>
          <EnterPaymentPage />
        </PaymentFlowProvider>
      </BrowserRouter>
    )

    expect(screen.getByText(/Pay Test Payee/i)).toBeInTheDocument()
    expect(screen.getByText(/04-00-04/)).toBeInTheDocument()
    expect(screen.getByLabelText(/From/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Amount/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Reference/i)).toBeInTheDocument()
  })

  it('displays selected account balance', async () => {
    render(
      <BrowserRouter>
        <PaymentFlowProvider>
          <EnterPaymentPage />
        </PaymentFlowProvider>
      </BrowserRouter>
    )

    // Account name and balance are in the select option - formatMinor adds comma
    const select = screen.getByLabelText(/From/i) as HTMLSelectElement
    
    // Wait for options to be rendered
    await waitFor(() => {
      expect(select.options.length).toBeGreaterThan(0)
    })
    
    expect(select.options[0].text).toMatch(/Current Account.*£1,248\.36/i)
  })

  it('allows amount input', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <PaymentFlowProvider>
          <EnterPaymentPage />
        </PaymentFlowProvider>
      </BrowserRouter>
    )

    const amountInput = screen.getByLabelText(/Amount/i)
    await user.type(amountInput, '50.00')

    expect(amountInput).toHaveValue('50.00')
  })

  it('shows error when amount exceeds balance', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <PaymentFlowProvider>
          <EnterPaymentPage />
        </PaymentFlowProvider>
      </BrowserRouter>
    )

    // Wait for accounts to load and select to populate
    await waitFor(() => {
      const select = screen.getByLabelText(/From/i) as HTMLSelectElement
      expect(select.options.length).toBeGreaterThan(0)
    })

    const amountInput = screen.getByLabelText(/Amount/i)
    // Enter amount that exceeds balance of 124836 pence (£1248.36)
    await user.type(amountInput, '5000.00')

    const payButton = screen.getByRole('button', { name: /Pay/i })
    await user.click(payButton)

    // Client-side balance check should trigger immediately
    await waitFor(() => {
      const errorText = screen.getByRole('alert')
      expect(errorText).toHaveTextContent(/You can pay up to/)
    })
  })

  it('disables pay button when amount is empty', () => {
    render(
      <BrowserRouter>
        <PaymentFlowProvider>
          <EnterPaymentPage />
        </PaymentFlowProvider>
      </BrowserRouter>
    )

    const payButton = screen.getByRole('button', { name: /Pay £0.00/i })
    expect(payButton).toBeDisabled()
  })

  it('navigates back when back button clicked', async () => {
    const user = userEvent.setup()
    render(
      <BrowserRouter>
        <PaymentFlowProvider>
          <EnterPaymentPage />
        </PaymentFlowProvider>
      </BrowserRouter>
    )

    const backButton = screen.getByLabelText(/Back/i)
    await user.click(backButton)

    expect(mockNavigate).toHaveBeenCalledWith(-1)
  })
})
