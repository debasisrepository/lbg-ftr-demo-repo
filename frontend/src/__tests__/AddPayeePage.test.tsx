import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { AddPayeePage } from '../pages/AddPayeePage'
import * as createPayeeHook from '../features/payees/useCreatePayee'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

vi.mock('../features/payees/useCreatePayee')

describe('AddPayeePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  const mockCreatePayee = vi.fn()

  it('should render form fields', () => {
    vi.spyOn(createPayeeHook, 'useCreatePayee').mockReturnValue({
      createPayee: mockCreatePayee,
      loading: false,
      error: null,
    })

    render(
      <BrowserRouter>
        <AddPayeePage />
      </BrowserRouter>
    )

    expect(screen.getByRole('heading', { level: 2, name: /Add a new payee/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/Payee name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Sort code/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Account number/i)).toBeInTheDocument()
  })

  it('should validate empty fields', async () => {
    const user = userEvent.setup()
    vi.spyOn(createPayeeHook, 'useCreatePayee').mockReturnValue({
      createPayee: mockCreatePayee,
      loading: false,
      error: null,
    })

    render(
      <BrowserRouter>
        <AddPayeePage />
      </BrowserRouter>
    )

    const submitButton = screen.getByText('Add payee')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Payee name is required/)).toBeInTheDocument()
    })

    expect(mockCreatePayee).not.toHaveBeenCalled()
  })

  it('should format sort code input', async () => {
    const user = userEvent.setup()
    vi.spyOn(createPayeeHook, 'useCreatePayee').mockReturnValue({
      createPayee: mockCreatePayee,
      loading: false,
      error: null,
    })

    render(
      <BrowserRouter>
        <AddPayeePage />
      </BrowserRouter>
    )

    const sortCodeInput = screen.getByLabelText('Sort code')
    await user.type(sortCodeInput, '123456')

    expect(sortCodeInput).toHaveValue('12-34-56')
  })

  it('should submit payee and show match outcome', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      payee: {
        payee_id: 'payee-1',
        customer_id: 'cust-1',
        profile_id: 'profile-1',
        payee_name: 'Test Payee',
        sort_code: '12-34-56',
        account_number_masked: '****5678',
        payee_type: 'personal',
        is_saved: true,
        status: 'active',
        last_verified_at: null,
        latest_cop_check: null,
      },
      cop_check: {
        cop_check_id: 'cop-1',
        outcome: 'match',
        suggested_name: null,
        policy_treatment: 'allow',
        checked_at: '2024-01-01T10:00:00Z',
        expires_at: null,
        customer_acknowledged_at: null,
      },
    }

    mockCreatePayee.mockResolvedValue(mockResponse)

    vi.spyOn(createPayeeHook, 'useCreatePayee').mockReturnValue({
      createPayee: mockCreatePayee,
      loading: false,
      error: null,
    })

    render(
      <BrowserRouter>
        <AddPayeePage />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText('Payee name'), 'Test Payee')
    await user.type(screen.getByLabelText('Sort code'), '123456')
    await user.type(screen.getByLabelText('Account number'), '12345678')

    const submitButton = screen.getByText('Add payee')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/Name matches/)).toBeInTheDocument()
    })

    expect(screen.getByText(/We checked the name against the account/)).toBeInTheDocument()
  })

  it('should show mismatch warning', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      payee: {
        payee_id: 'payee-1',
        customer_id: 'cust-1',
        profile_id: 'profile-1',
        payee_name: 'Test Payee',
        sort_code: '12-34-56',
        account_number_masked: '****5678',
        payee_type: 'personal',
        is_saved: true,
        status: 'active',
        last_verified_at: null,
        latest_cop_check: null,
      },
      cop_check: {
        cop_check_id: 'cop-1',
        outcome: 'mismatch',
        suggested_name: 'Different Name',
        policy_treatment: 'warn',
        checked_at: '2024-01-01T10:00:00Z',
        expires_at: null,
        customer_acknowledged_at: null,
      },
    }

    mockCreatePayee.mockResolvedValue(mockResponse)

    vi.spyOn(createPayeeHook, 'useCreatePayee').mockReturnValue({
      createPayee: mockCreatePayee,
      loading: false,
      error: null,
    })

    render(
      <BrowserRouter>
        <AddPayeePage />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText('Payee name'), 'Test Payee')
    await user.type(screen.getByLabelText('Sort code'), '123456')
    await user.type(screen.getByLabelText('Account number'), '12345678')

    const submitButton = screen.getByText('Add payee')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/the name doesn't match/)).toBeInTheDocument()
    })

    expect(screen.getByText(/Paying the wrong account could mean/)).toBeInTheDocument()
  })

  it('should show unavailable outcome', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      payee: {
        payee_id: 'payee-1',
        customer_id: 'cust-1',
        profile_id: 'profile-1',
        payee_name: 'Test Payee',
        sort_code: '12-34-56',
        account_number_masked: '****5678',
        payee_type: 'personal',
        is_saved: false,
        status: 'pending_verification',
        last_verified_at: null,
        latest_cop_check: null,
      },
      cop_check: {
        cop_check_id: 'cop-1',
        outcome: 'unavailable',
        suggested_name: null,
        policy_treatment: 'warn',
        checked_at: '2024-01-01T10:00:00Z',
        expires_at: null,
        customer_acknowledged_at: null,
      },
    }

    mockCreatePayee.mockResolvedValue(mockResponse)

    vi.spyOn(createPayeeHook, 'useCreatePayee').mockReturnValue({
      createPayee: mockCreatePayee,
      loading: false,
      error: null,
    })

    render(
      <BrowserRouter>
        <AddPayeePage />
      </BrowserRouter>
    )

    await user.type(screen.getByLabelText('Payee name'), 'Test Payee')
    await user.type(screen.getByLabelText('Sort code'), '123456')
    await user.type(screen.getByLabelText('Account number'), '12345678')

    const submitButton = screen.getByText('Add payee')
    await user.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText(/We couldn't check this payee/)).toBeInTheDocument()
    })

    expect(screen.getByText('Try again')).toBeInTheDocument()
    expect(screen.getByText('Back to payees')).toBeInTheDocument()
  })
})
