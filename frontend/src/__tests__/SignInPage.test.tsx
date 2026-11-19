/**
 * SignInPage component tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { SignInPage } from '../pages/SignInPage'
import * as apiClient from '../lib/api-client'
import * as deviceBridge from '../lib/device-bridge'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: {} }),
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

function renderSignInPage() {
  return render(
    <BrowserRouter>
      <SignInPage />
    </BrowserRouter>
  )
}

describe('SignInPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
    sessionStorage.clear()
    vi.mocked(deviceBridge.deviceBridge.isBiometricAvailable).mockResolvedValue(false)
    vi.mocked(deviceBridge.deviceBridge.getDeviceIdentifier).mockResolvedValue('test-device-id')
  })

  it('renders the sign-in form', () => {
    renderSignInPage()

    expect(screen.getByRole('heading', { name: /login/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /continue/i })).toBeInTheDocument()
  })

  it('shows validation errors when fields are empty', async () => {
    const user = userEvent.setup()
    renderSignInPage()

    const continueButton = screen.getByRole('button', { name: /continue/i })
    await user.click(continueButton)

    expect(await screen.findByText(/error: enter your username/i)).toBeInTheDocument()
    expect(await screen.findByText(/error: enter your password/i)).toBeInTheDocument()
  })

  it('submits credentials and navigates to proof page on success', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      session_id: 'test-session-id',
      customer_id: 'test-customer-id',
      auth_level: 'password_only',
      requires_proof: true,
      proof_methods: ['passcode', 'biometric'],
      proof_deadline: '2024-01-01T12:00:00Z',
    }

    vi.mocked(apiClient.apiClient.post).mockResolvedValue(mockResponse)

    renderSignInPage()

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const continueButton = screen.getByRole('button', { name: /continue/i })

    await user.type(usernameInput, 'sasha.patel@gmail.com')
    await user.type(passwordInput, 'Demo1234!')
    await user.click(continueButton)

    await waitFor(() => {
      expect(apiClient.apiClient.post).toHaveBeenCalledWith(
        '/auth/sign-in',
        {
          username: 'sasha.patel@gmail.com',
          password: 'Demo1234!',
          device_id: 'test-device-id',
        },
        { skipAuth: true }
      )
      expect(mockNavigate).toHaveBeenCalledWith('/proof', {
        state: {
          session_id: 'test-session-id',
          proof_methods: ['passcode', 'biometric'],
        },
      })
    })
  })

  it('shows generic error message on authentication failure', async () => {
    const user = userEvent.setup()
    vi.mocked(apiClient.apiClient.post).mockRejectedValue(
      new Error('Invalid credentials')
    )

    renderSignInPage()

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const continueButton = screen.getByRole('button', { name: /continue/i })

    await user.type(usernameInput, 'wrong@example.com')
    await user.type(passwordInput, 'wrongpass')
    await user.click(continueButton)

    expect(
      await screen.findByText(/we couldn't log you in with those details/i)
    ).toBeInTheDocument()
  })

  it('toggles password visibility', async () => {
    const user = userEvent.setup()
    renderSignInPage()

    const passwordInput = screen.getByLabelText(/password/i) as HTMLInputElement
    await user.type(passwordInput, 'testpass')

    expect(passwordInput.type).toBe('password')

    const showPasswordLink = screen.getByText(/show password/i)
    await user.click(showPasswordLink)

    expect(passwordInput.type).toBe('text')

    const hidePasswordLink = screen.getByText(/hide password/i)
    await user.click(hidePasswordLink)

    expect(passwordInput.type).toBe('password')
  })

  it('clears error messages when user starts typing', async () => {
    const user = userEvent.setup()
    renderSignInPage()

    const continueButton = screen.getByRole('button', { name: /continue/i })
    await user.click(continueButton)

    expect(await screen.findByText(/error: enter your username/i)).toBeInTheDocument()

    const usernameInput = screen.getByLabelText(/username/i)
    await user.clear(usernameInput)
    await user.type(usernameInput, 'a')

    // Wait a moment for state to update
    await waitFor(() => {
      expect(screen.queryByText(/error: enter your username/i)).not.toBeInTheDocument()
    })
  })

  it('stores last username in localStorage after successful sign-in', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      session_id: 'test-session-id',
      customer_id: 'test-customer-id',
      auth_level: 'password_only',
      requires_proof: true,
      proof_methods: ['passcode'],
      proof_deadline: '2024-01-01T12:00:00Z',
    }

    vi.mocked(apiClient.apiClient.post).mockResolvedValue(mockResponse)

    renderSignInPage()

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const continueButton = screen.getByRole('button', { name: /continue/i })

    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'testpass')
    await user.click(continueButton)

    await waitFor(() => {
      expect(localStorage.getItem('last_username')).toBe('test@example.com')
    })
  })

  it('stores session info in sessionStorage for proof page', async () => {
    const user = userEvent.setup()
    const mockResponse = {
      session_id: 'session-123',
      customer_id: 'customer-456',
      auth_level: 'password_only',
      requires_proof: true,
      proof_methods: ['passcode'],
      proof_deadline: '2024-01-01T12:00:00Z',
    }

    vi.mocked(apiClient.apiClient.post).mockResolvedValue(mockResponse)

    renderSignInPage()

    const usernameInput = screen.getByLabelText(/username/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const continueButton = screen.getByRole('button', { name: /continue/i })

    await user.type(usernameInput, 'test@example.com')
    await user.type(passwordInput, 'testpass')
    await user.click(continueButton)

    await waitFor(() => {
      expect(sessionStorage.getItem('pending_session_id')).toBe('session-123')
      expect(sessionStorage.getItem('pending_customer_id')).toBe('customer-456')
    })
  })
})
