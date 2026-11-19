/**
 * Proof Page (FR-002)
 * - 6-digit passcode entry with numeric keypad
 * - Biometric prompt via DeviceBridge
 * - Wrong passcode with attempts remaining
 * - Passcode paused after 3 attempts with password fallback
 * - Device not trusted with safe next step
 */

import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiClient } from '../lib/api-client'
import { deviceBridge } from '../lib/device-bridge'
import sharedConfig from '../../../shared_config.json'

interface ProofResponse {
  session_id: string
  auth_level: string
  access_token: string
  token_type: string
  expires_in: number
  active_profile_id?: string
}

interface ProofLocationState {
  session_id?: string
  proof_methods?: string[]
  device_not_trusted?: boolean
}

export function ProofPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const locationState = (location.state as ProofLocationState) || {}
  
  const [passcode, setPasscode] = useState('')
  const [showPasscode, setShowPasscode] = useState(false)
  const [passcodeError, setPasscodeError] = useState('')
  const [attemptsRemaining, setAttemptsRemaining] = useState<number | null>(null)
  const [isPasscodePaused, setIsPasscodePaused] = useState(false)
  const [deviceNotTrusted, setDeviceNotTrusted] = useState(
    locationState.device_not_trusted || false
  )
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId] = useState<string | null>(
    locationState.session_id || sessionStorage.getItem('pending_session_id')
  )

  // Check for device trust issues
  useEffect(() => {
    if (!sessionId && !deviceNotTrusted) {
      // No valid session, redirect to sign-in
      navigate('/login', { replace: true })
    }
  }, [sessionId, deviceNotTrusted, navigate])

  const handlePasscodeInput = (digit: string) => {
    if (passcode.length < 6) {
      const newPasscode = passcode + digit
      setPasscode(newPasscode)
      setPasscodeError('')
      setAttemptsRemaining(null)

      // Auto-submit when 6 digits entered
      if (newPasscode.length === 6) {
        submitProof(newPasscode, 'passcode')
      }
    }
  }

  const handleDelete = () => {
    setPasscode(passcode.slice(0, -1))
    setPasscodeError('')
    setAttemptsRemaining(null)
  }

  const submitProof = async (proofValue: string, proofType: 'passcode' | 'biometric') => {
    if (!sessionId) {
      setDeviceNotTrusted(true)
      return
    }

    setIsLoading(true)

    try {
      const deviceIdentifier = await deviceBridge.getDeviceIdentifier()

      const response = await apiClient.post<ProofResponse>(
        '/auth/proof',
        {
          session_id: sessionId,
          proof_type: proofType,
          proof_value: proofValue,
          device_id: deviceIdentifier,
        },
        { skipAuth: true }
      )

      // Store JWT token
      localStorage.setItem(sharedConfig.auth_storage_key, response.access_token)
      
      // Clear pending session
      sessionStorage.removeItem('pending_session_id')
      sessionStorage.removeItem('pending_customer_id')

      // Navigate to accounts overview
      navigate('/accounts', { replace: true })
    } catch (error: unknown) {
      // Handle wrong passcode error
      const errorObj = error as { status?: number; detail?: string }
      
      // Check for passcode paused
      if (errorObj.detail?.includes('paused') || errorObj.detail?.includes('lockout') || errorObj.status === 429) {
        setIsPasscodePaused(true)
        setPasscodeError(
          "Error: For your security, we've paused passcode login. Log in with your username and password instead."
        )
        setPasscode('')
      } else if (errorObj.detail?.includes('device') || errorObj.detail?.includes('trust')) {
        // Device not trusted
        setDeviceNotTrusted(true)
      } else if (errorObj.status === 401 || errorObj.status === 400) {
        // Failed proof attempt - try to parse attempts from detail message
        let remainingAttempts: number | null = null
        
        if (errorObj.detail) {
          const match = errorObj.detail.match(/(\d+)\s+attempt/)
          if (match) {
            remainingAttempts = parseInt(match[1], 10)
          }
        }
        
        // If backend didn't provide attempts, use client-side counter
        if (remainingAttempts === null) {
          remainingAttempts = attemptsRemaining === null ? 2 : attemptsRemaining - 1
        }
        
        if (remainingAttempts > 0) {
          setPasscodeError(
            `Error: That passcode isn't right. You have ${remainingAttempts} ${
              remainingAttempts === 1 ? 'attempt' : 'attempts'
            } left.`
          )
          setAttemptsRemaining(remainingAttempts)
          setPasscode('')
        } else {
          // Passcode paused after exhausting attempts
          setIsPasscodePaused(true)
          setPasscodeError(
            "Error: For your security, we've paused passcode login. Log in with your username and password instead."
          )
          setPasscode('')
        }
      } else {
        // Generic error
        setPasscodeError("Error: That passcode isn't right. Please try again.")
        setPasscode('')
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleUseFaceId = async () => {
    setIsLoading(true)
    setPasscodeError('')

    try {
      const challenge = 'biometric-challenge-' + Date.now()
      const biometricResult = await deviceBridge.requestBiometricProof(challenge)

      if (biometricResult.success && biometricResult.proof_data) {
        await submitProof(biometricResult.proof_data, 'biometric')
      } else {
        // Biometric not available, stay on passcode
        setPasscodeError('Error: Biometric authentication is not available.')
      }
    } catch {
      setPasscodeError('Error: Biometric authentication failed.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleLoginWithUsername = () => {
    // Clear pending session
    sessionStorage.removeItem('pending_session_id')
    sessionStorage.removeItem('pending_customer_id')
    navigate('/login', { replace: true })
  }

  // Device not trusted screen
  if (deviceNotTrusted) {
    return (
      <div className="min-h-screen bg-white flex flex-col">
        <div className="h-11 bg-white flex items-center px-6 text-sm font-semibold">
          9:41
        </div>
        <div className="min-h-12 flex items-center px-2">
          <button
            type="button"
            aria-label="Back"
            className="w-11 h-11 border-0 bg-transparent flex items-center justify-center text-[#161616]"
            onClick={handleLoginWithUsername}
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
          <h2 className="text-[28px] leading-9 font-semibold mt-4 mb-2">
            We couldn't confirm it's you
          </h2>
          <div
            className="border border-[#8d8d8d] border-l-4 border-l-[#161616] bg-[#f4f4f4] p-3 mb-6 text-sm leading-5"
            role="alert"
          >
            <strong>Error:</strong> We can't confirm this device yet, so your accounts and
            payments are not available. Log in with your username and password to try again.
          </div>
          <button
            onClick={handleLoginWithUsername}
            className="w-full min-h-[52px] bg-[#161616] text-white font-semibold border-2 border-[#161616]"
          >
            Login with username
          </button>
          <button
            onClick={(e) => {
              e.preventDefault()
              alert('Contact support feature coming soon')
            }}
            className="w-full min-h-[52px] bg-white text-[#161616] font-semibold border-2 border-[#161616] mt-2"
          >
            Contact the bank
          </button>
          <div className="h-6"></div>
        </div>
      </div>
    )
  }

  // Passcode entry screen
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="h-11 bg-white flex items-center px-6 text-sm font-semibold">
        9:41
      </div>
      <div className="min-h-12 flex items-center px-2">
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
        <h2 className="text-[28px] leading-9 font-semibold mt-4 mb-2">
          Enter your passcode
        </h2>
        {!passcodeError && (
          <p className="text-[#525252] mb-6">
            Enter the 6-digit passcode you created when you opened your account.
          </p>
        )}

        {/* Passcode boxes */}
        <div className="flex gap-2 mb-3" aria-label={`Passcode, ${passcode.length} of 6 digits entered`}>
          {[0, 1, 2, 3, 4, 5].map((index) => {
            const isFilled = index < passcode.length
            const isFocused = index === passcode.length && !passcodeError
            const hasError = passcodeError !== ''

            return (
              <div
                key={index}
                className={`flex-1 h-14 flex items-center justify-center text-2xl font-semibold ${
                  hasError
                    ? 'border-2 border-[#c62828] bg-white'
                    : isFocused
                    ? 'border-[3px] border-[#161616] bg-white'
                    : 'border border-[#8d8d8d] bg-[#f4f4f4]'
                }`}
              >
                {isFilled && (showPasscode ? passcode[index] : '●')}
              </div>
            )
          })}
        </div>

        {/* Error message */}
        {passcodeError && (
          <p className="text-sm leading-5 text-[#c62828] font-semibold mt-2 mb-3" role="alert">
            {passcodeError}
          </p>
        )}

        {/* Links */}
        <div className="flex justify-between mt-2 mb-3 text-sm">
          <a
            href="#"
            className="text-[#161616] underline inline-block min-h-[44px] leading-[44px]"
            onClick={(e) => e.preventDefault()}
          >
            Forgotten your passcode?
          </a>
          <a
            href="#"
            className="text-[#161616] underline inline-block min-h-[44px] leading-[44px]"
            onClick={(e) => {
              e.preventDefault()
              setShowPasscode(!showPasscode)
            }}
          >
            {showPasscode ? 'Hide passcode' : 'Show passcode'}
          </a>
        </div>

        {/* Face ID option */}
        {!isPasscodePaused && (
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              handleUseFaceId()
            }}
            className="flex items-center justify-center gap-2 min-h-12 font-semibold text-base underline mb-2"
          >
            <svg
              viewBox="0 0 24 24"
              aria-hidden="true"
              className="w-6 h-6 stroke-current fill-none stroke-2"
            >
              <path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4M9 10v2M15 10v2M9 16c1.5 1 4.5 1 6 0" />
            </svg>
            Use Face ID instead
          </a>
        )}

        {/* Password fallback button when paused */}
        {isPasscodePaused && (
          <button
            onClick={handleLoginWithUsername}
            className="w-full min-h-[52px] bg-[#161616] text-white font-semibold border-2 border-[#161616] mt-2"
          >
            Login with username
          </button>
        )}

        <div className="flex-1 min-h-3"></div>

        {/* Numeric keypad */}
        <div
          className="grid grid-cols-3 gap-[1px] bg-[#c6c6c6] border-t border-[#c6c6c6] -mx-6 mt-3"
          aria-label="Numeric keypad"
        >
          {/* Row 1 */}
          <button
            type="button"
            onClick={() => handlePasscodeInput('1')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            1
          </button>
          <button
            type="button"
            onClick={() => handlePasscodeInput('2')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            2<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">ABC</small>
          </button>
          <button
            type="button"
            onClick={() => handlePasscodeInput('3')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            3<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">DEF</small>
          </button>

          {/* Row 2 */}
          <button
            type="button"
            onClick={() => handlePasscodeInput('4')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            4<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">GHI</small>
          </button>
          <button
            type="button"
            onClick={() => handlePasscodeInput('5')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            5<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">JKL</small>
          </button>
          <button
            type="button"
            onClick={() => handlePasscodeInput('6')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            6<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">MNO</small>
          </button>

          {/* Row 3 */}
          <button
            type="button"
            onClick={() => handlePasscodeInput('7')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            7<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">PQRS</small>
          </button>
          <button
            type="button"
            onClick={() => handlePasscodeInput('8')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            8<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">TUV</small>
          </button>
          <button
            type="button"
            onClick={() => handlePasscodeInput('9')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex flex-col items-center justify-center text-2xl font-semibold leading-6"
          >
            9<small className="text-[10px] leading-3 font-normal text-[#525252] tracking-wider">WXYZ</small>
          </button>

          {/* Row 4 */}
          <div className="bg-[#f4f4f4] h-[60px]"></div>
          <button
            type="button"
            onClick={() => handlePasscodeInput('0')}
            disabled={isLoading || isPasscodePaused}
            className="bg-[#f4f4f4] h-[60px] flex items-center justify-center text-2xl font-semibold leading-6"
          >
            0
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={isLoading || isPasscodePaused}
            aria-label="Delete"
            className="bg-[#f4f4f4] h-[60px] flex items-center justify-center text-2xl font-semibold"
          >
            ⌫
          </button>
        </div>
      </div>
    </div>
  )
}
