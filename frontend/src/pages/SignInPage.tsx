/**
 * Sign In Page (FR-001)
 * - Username and password authentication
 * - Empty field validation
 * - Generic error messages
 * - Face ID prompt for returning users
 */

import React, { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiClient } from '../lib/api-client'
import { deviceBridge } from '../lib/device-bridge'

interface SignInResponse {
  session_id: string
  customer_id: string
  auth_level: string
  requires_proof: boolean
  proof_methods: string[]
  proof_deadline: string
}

interface LocationState {
  from?: {
    pathname: string
  }
}

export function SignInPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [usernameError, setUsernameError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [genericError, setGenericError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showFaceId, setShowFaceId] = useState(false)

  // Check for returning user on mount
  React.useEffect(() => {
    const checkReturningUser = async () => {
      const storedUsername = localStorage.getItem('last_username')
      const storedDeviceId = localStorage.getItem('device_identifier')
      const biometricAvailable = await deviceBridge.isBiometricAvailable()
      
      if (storedUsername && storedDeviceId && biometricAvailable) {
        setShowFaceId(true)
      }
    }
    checkReturningUser()
  }, [])

  const handleContinue = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Clear previous errors
    setUsernameError('')
    setPasswordError('')
    setGenericError('')

    // Empty field validation
    let hasError = false
    if (!username.trim()) {
      setUsernameError('Error: Enter your username')
      hasError = true
    }
    if (!password.trim()) {
      setPasswordError('Error: Enter your password')
      hasError = true
    }

    if (hasError) {
      return
    }

    setIsLoading(true)

    try {
      const deviceIdentifier = await deviceBridge.getDeviceIdentifier()
      
      const response = await apiClient.post<SignInResponse>(
        '/auth/sign-in',
        {
          username,
          password,
          device_id: deviceIdentifier,
        },
        { skipAuth: true }
      )

      // Store username for returning user detection
      localStorage.setItem('last_username', username)
      
      // Store session info for proof page
      sessionStorage.setItem('pending_session_id', response.session_id)
      sessionStorage.setItem('pending_customer_id', response.customer_id)
      
      // Navigate to proof page
      if (response.requires_proof) {
        navigate('/proof', { 
          state: { 
            session_id: response.session_id,
            proof_methods: response.proof_methods,
          } 
        })
      } else {
        // Should not happen for this flow, but handle it
        navigate((location.state as LocationState)?.from?.pathname || '/accounts')
      }
    } catch {
      // Generic error message per FR-001 acceptance criterion (matches wireframe D text)
      setGenericError("We couldn't log you in with those details. Check them and try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleFaceIdLogin = async () => {
    setIsLoading(true)
    setGenericError('')

    try {
      const challenge = 'face-id-challenge-' + Date.now()
      const biometricResult = await deviceBridge.requestBiometricProof(challenge)

      if (!biometricResult.success) {
        // Fall back to regular sign-in
        setShowFaceId(false)
        return
      }

      // This would normally go through the full auth flow
      // For now, just show regular sign-in
      setShowFaceId(false)
    } catch {
      setShowFaceId(false)
    } finally {
      setIsLoading(false)
    }
  }

  const handleNotSasha = () => {
    setShowFaceId(false)
    localStorage.removeItem('last_username')
  }

  // Face ID screen for returning users
  if (showFaceId) {
    const displayName = localStorage.getItem('last_username')?.split('@')[0] || 'User'
    const firstName = displayName.charAt(0).toUpperCase() + displayName.slice(1)

    return (
      <div className="min-h-screen bg-[#393939] flex flex-col">
        <div className="h-11 flex items-center px-6 text-sm font-semibold text-white">
          9:41
        </div>
        <div className="flex-1 flex flex-col items-center px-6 pt-12">
          <div className="flex items-center gap-2 font-semibold text-xl text-white mt-5">
            <span className="w-10 h-10 border-2 border-white flex items-center justify-center text-sm">
              YB
            </span>
            <span>Your Bank</span>
          </div>
          <p className="text-xs text-[#e0e0e0] mt-2">Full-screen photo background</p>
          <div className="mt-auto w-full max-w-md bg-white text-[#161616] p-6 border border-[#8d8d8d]">
            <h2 className="text-2xl leading-8 font-semibold mb-2">
              Welcome back, {firstName}
            </h2>
            <a
              href="#"
              onClick={(e) => {
                e.preventDefault()
                handleNotSasha()
              }}
              className="text-[#161616] underline inline-block min-h-[44px] leading-[44px]"
            >
              Not {firstName}? Log in with your details
            </a>
            <button
              onClick={handleFaceIdLogin}
              disabled={isLoading}
              className="w-full min-h-[52px] bg-[#161616] text-white font-semibold border-2 border-[#161616] mt-3"
            >
              Login with Face ID
            </button>
            <button
              onClick={() => setShowFaceId(false)}
              disabled={isLoading}
              className="w-full min-h-[52px] bg-white text-[#161616] font-semibold border-2 border-[#161616] mt-2"
            >
              Use passcode
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Regular sign-in screen
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="h-11 bg-white flex items-center px-6 text-sm font-semibold">
        9:41
      </div>
      <div className="min-h-12 flex items-center px-2 gap-2">
        <button
          type="button"
          aria-label="Back"
          className="w-11 h-11 border-0 bg-transparent flex items-center justify-center text-[#161616]"
          onClick={() => navigate(-1)}
        >
          <svg
            viewBox="0 0 24 24"
            aria-hidden="true"
            className="w-6 h-6 stroke-current fill-none stroke-2"
            style={{ strokeLinecap: 'square' }}
          >
            <path d="M19 12H5M11 5l-7 7 7 7" />
          </svg>
        </button>
      </div>
      <div className="flex-1 px-6 py-2 flex flex-col">
        <h2 className="text-[28px] leading-9 font-semibold mt-4 mb-2">Login</h2>
        <p className="text-[#525252] mb-6">
          Use the username and password you set up when you opened your account.
        </p>

        {genericError && (
          <div
            className="border border-[#8d8d8d] border-l-4 border-l-[#161616] bg-[#f4f4f4] p-3 mb-6 text-sm leading-5"
            role="alert"
          >
            <strong>Error:</strong> {genericError}
          </div>
        )}

        <form onSubmit={handleContinue}>
          <div className="mb-6">
            <label
              htmlFor="username"
              className="block text-sm leading-5 font-semibold mb-2"
            >
              Username
            </label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => {
                setUsername(e.target.value)
                setUsernameError('')
                setGenericError('')
              }}
              className={`w-full h-[52px] border bg-[#f4f4f4] px-4 text-base text-[#161616] ${
                usernameError
                  ? 'border-2 border-[#c62828] bg-white'
                  : 'border-[#8d8d8d]'
              }`}
              aria-invalid={!!usernameError}
              aria-describedby={usernameError ? 'username-error' : undefined}
            />
            {usernameError && (
              <p id="username-error" className="text-sm leading-5 text-[#c62828] font-semibold mt-2">
                {usernameError}
              </p>
            )}
          </div>

          <div className="mb-6">
            <label
              htmlFor="password"
              className="block text-sm leading-5 font-semibold mb-2"
            >
              Password
            </label>
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => {
                setPassword(e.target.value)
                setPasswordError('')
                setGenericError('')
              }}
              className={`w-full h-[52px] border bg-[#f4f4f4] px-4 text-base text-[#161616] ${
                passwordError
                  ? 'border-2 border-[#c62828] bg-white'
                  : 'border-[#8d8d8d]'
              }`}
              aria-invalid={!!passwordError}
              aria-describedby={passwordError ? 'password-error' : undefined}
            />
            {passwordError && (
              <p id="password-error" className="text-sm leading-5 text-[#c62828] font-semibold mt-2">
                {passwordError}
              </p>
            )}
          </div>

          <div className="flex justify-between mb-6 text-sm">
            <a
              href="#"
              className="text-[#161616] underline inline-block min-h-[44px] leading-[44px]"
              onClick={(e) => e.preventDefault()}
            >
              Forgotten your details?
            </a>
            <a
              href="#"
              className="text-[#161616] underline inline-block min-h-[44px] leading-[44px]"
              onClick={(e) => {
                e.preventDefault()
                setShowPassword(!showPassword)
              }}
            >
              {showPassword ? 'Hide password' : 'Show password'}
            </a>
          </div>

          <div className="flex-1 min-h-6"></div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full min-h-[52px] bg-[#161616] text-white font-semibold border-2 border-[#161616] mt-3 disabled:opacity-50"
          >
            {isLoading ? 'Loading...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}
