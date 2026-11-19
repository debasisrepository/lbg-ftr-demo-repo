/**
 * ProofPage component tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { ProofPage } from '../pages/ProofPage'
import * as apiClient from '../lib/api-client'
import * as deviceBridge from '../lib/device-bridge'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({
      state: {
        session_id: 'test-session-id',
        proof_methods: ['passcode', 'biometric'],
      },
    }),
  }
})

vi.mock('../lib/api-client', () => ({
  apiClient: {
    post: vi.fn(),
  },
}))

vi.mock('../lib/device-bridge', () => ({
  deviceBridge: {
    isBiometricAvailable: vi.fn(),
    requestBiometricProof: vi.fn(),
    getDeviceIdentifier: vi.fn(),
  },
}))

function renderProofPage() {
  return render(
    <BrowserRouter>
      <ProofPage />
    </BrowserRouter>
  )
}

describe('ProofPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
    sessionStorage.setItem('pending_session_id', 'test-session-id')
    vi.mocked(deviceBridge.deviceBridge.getDeviceIdentifier).mockResolvedValue('test-device-id')
  })

  it('renders the passcode entry screen', () => {
    renderProofPage()

    expect(screen.getByRole('heading', { name: /enter your passcode/i })).toBeInTheDocument()
    expect(
      screen.getByText(/enter the 6-digit passcode you created/i)
    ).toBeInTheDocument()
  })

  it('displays 6 passcode boxes', () => {
    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    expect(keypad).toBeInTheDocument()

    // Check that passcode display exists
    const passcodeDisplay = screen.getByLabelText(/passcode, 0 of 6 digits entered/i)
    expect(passcodeDisplay).toBeInTheDocument()
  })

  it('allows entering digits via keypad', async () => {
    const user = userEvent.setup()
    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    const button1 = buttons.find(b => b.textContent?.includes('1') && !b.textContent?.includes('ABC'))

    await user.click(button1!)

    await waitFor(() => {
      expect(screen.getByLabelText(/passcode, 1 of 6 digits entered/i)).toBeInTheDocument()
    })
  })

  it('submits proof when 6 digits are entered', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      session_id: 'test-session-id',
      auth_level: 'proven',
      access_token: 'test-jwt-token',
      token_type: 'Bearer',
      expires_in: 1800,
      active_profile_id: 'test-profile-id',
    }

    vi.mocked(apiClient.apiClient.post).mockResolvedValue(mockResponse)

    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    
    // Click buttons 1-6
    for (let i = 1; i <= 6; i++) {
      const button = buttons.find(b => 
        b.textContent?.trim().startsWith(String(i)) && 
        (i === 1 || !b.textContent?.includes('0'))
      )
      await user.click(button!)
    }

    await waitFor(() => {
      expect(apiClient.apiClient.post).toHaveBeenCalledWith(
        '/auth/proof',
        {
          session_id: 'test-session-id',
          proof_type: 'passcode',
          proof_value: '123456',
          device_id: 'test-device-id',
        },
        { skipAuth: true }
      )
      expect(localStorage.getItem('lbg_ftr_demo_auth_token')).toBe('test-jwt-token')
      expect(mockNavigate).toHaveBeenCalledWith('/accounts', { replace: true })
    })
  })

  it('shows error message for wrong passcode with attempts remaining', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.apiClient.post).mockRejectedValue({
      status: 400,
      detail: 'Wrong passcode. You have 2 attempts left.',
    })

    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    
    // Enter 6 digits
    for (let i = 1; i <= 6; i++) {
      const button = buttons.find(b => 
        b.textContent?.trim().startsWith(String(i)) && 
        (i === 1 || !b.textContent?.includes('0'))
      )
      await user.click(button!)
    }

    await waitFor(() => {
      expect(
        screen.getByText(/that passcode isn't right.*2 attempts left/i)
      ).toBeInTheDocument()
    })
  })

  it('shows passcode paused message and fallback button after 3 failures', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.apiClient.post).mockRejectedValue({
      status: 429,
      detail: 'Passcode entry is paused. Please use password sign-in.',
    })

    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    
    // Enter 6 digits
    for (let i = 1; i <= 6; i++) {
      const button = buttons.find(b => 
        b.textContent?.trim().startsWith(String(i)) && 
        (i === 1 || !b.textContent?.includes('0'))
      )
      await user.click(button!)
    }

    await waitFor(() => {
      expect(
        screen.getByText(/for your security.*paused passcode login/i)
      ).toBeInTheDocument()
      expect(
        screen.getByRole('button', { name: /login with username/i })
      ).toBeInTheDocument()
    })
  })

  it('allows deleting entered digits', async () => {
    const user = userEvent.setup()
    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    const button1 = buttons.find(b => b.textContent?.trim().startsWith('1'))
    const deleteButton = within(keypad).getByRole('button', { name: /delete/i })

    await user.click(button1!)
    await user.click(button1!)

    await waitFor(() => {
      expect(screen.getByLabelText(/passcode, 2 of 6 digits entered/i)).toBeInTheDocument()
    })

    await user.click(deleteButton)

    await waitFor(() => {
      expect(screen.getByLabelText(/passcode, 1 of 6 digits entered/i)).toBeInTheDocument()
    })
  })

  it('toggles passcode visibility', async () => {
    const user = userEvent.setup()
    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    const button1 = buttons.find(b => b.textContent?.trim().startsWith('1'))

    // Enter a digit
    await user.click(button1!)

    // By default, passcode is masked - we see bullets
    // After clicking show, we should see the digit
    const showLink = screen.getByText(/show passcode/i)
    await user.click(showLink)

    // Now it should show "Hide passcode"
    expect(screen.getByText(/hide passcode/i)).toBeInTheDocument()
  })

  it('navigates to login when fallback button is clicked on paused screen', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.apiClient.post).mockRejectedValue({
      status: 429,
      detail: 'Passcode entry is paused.',
    })

    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    
    // Enter 6 digits to trigger error
    for (let i = 1; i <= 6; i++) {
      const button = buttons.find(b => 
        b.textContent?.trim().startsWith(String(i)) && 
        (i === 1 || !b.textContent?.includes('0'))
      )
      await user.click(button!)
    }

    await waitFor(() => {
      expect(
        screen.getByRole('button', { name: /login with username/i })
      ).toBeInTheDocument()
    })

    const fallbackButton = screen.getByRole('button', { name: /login with username/i })
    await user.click(fallbackButton)

    expect(mockNavigate).toHaveBeenCalledWith('/login', { replace: true })
  })

  it('clears session storage after successful proof', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      session_id: 'test-session-id',
      auth_level: 'proven',
      access_token: 'test-jwt-token',
      token_type: 'Bearer',
      expires_in: 1800,
    }

    vi.mocked(apiClient.apiClient.post).mockResolvedValue(mockResponse)

    sessionStorage.setItem('pending_session_id', 'session-123')
    sessionStorage.setItem('pending_customer_id', 'customer-456')

    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    
    // Enter 6 digits
    for (let i = 1; i <= 6; i++) {
      const button = buttons.find(b => 
        b.textContent?.trim().startsWith(String(i)) && 
        (i === 1 || !b.textContent?.includes('0'))
      )
      await user.click(button!)
    }

    await waitFor(() => {
      expect(sessionStorage.getItem('pending_session_id')).toBeNull()
      expect(sessionStorage.getItem('pending_customer_id')).toBeNull()
    })
  })

  it('clears passcode boxes after error', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.apiClient.post).mockRejectedValue({
      status: 400,
      detail: 'Wrong passcode. You have 2 attempts left.',
    })

    renderProofPage()

    const keypad = screen.getByLabelText(/numeric keypad/i)
    const buttons = within(keypad).getAllByRole('button')
    
    // Enter 6 digits
    for (let i = 1; i <= 6; i++) {
      const button = buttons.find(b => 
        b.textContent?.trim().startsWith(String(i)) && 
        (i === 1 || !b.textContent?.includes('0'))
      )
      await user.click(button!)
    }

    await waitFor(() => {
      // After error, boxes should be cleared
      expect(screen.getByLabelText(/passcode, 0 of 6 digits entered/i)).toBeInTheDocument()
    })
  })
})
