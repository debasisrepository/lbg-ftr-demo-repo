/**
 * Step-Up Authentication Page
 * Additional authentication for sensitive actions (payments, payee changes)
 * - 6-digit passcode entry
 * - Biometric proof
 * - Challenge verification
 */

import React, { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiClient } from '../lib/api-client'
import { deviceBridge } from '../lib/device-bridge'
import { useAuth } from '../lib/auth-context'

interface StepUpChallengeResponse {
  challenge_reference: string
  purpose: string
  method: string
  expires_at: string
}

interface VerifyStepUpResponse {
  verified: boolean
  elevated_until: string
  auth_level: string
}

interface StepUpLocationState {
  purpose?: string
  returnPath?: string
}

export function StepUpPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user } = useAuth()
  const locationState = (location.state as StepUpLocationState) || {}
  
  const [passcode, setPasscode] = useState('')
  const [showPasscode, setShowPasscode] = useState(false)
  const [passcodeError, setPasscodeError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [challengeReference, setChallengeReference] = useState<string | null>(null)
  const [purpose] = useState(locationState.purpose || 'payment_approval')
  const [returnPath] = useState(locationState.returnPath || '/accounts')

  useEffect(() => {
    // Create step-up challenge on mount
    createChallenge()
  }, [])

  const createChallenge = async () => {
    if (!user) {
      navigate('/login', { replace: true })
      return
    }

    setIsLoading(true)
    try {
      const response = await apiClient.post<StepUpChallengeResponse>(
        '/auth/step-up',
        {
          purpose,
          preferred_method: 'passcode',
        }
      )
      setChallengeReference(response.challenge_reference)
    } catch (error) {
      console.error('Failed to create step-up challenge:', error)
      setPasscodeError('Failed to initialize authentication. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handlePasscodeInput = (digit: string) => {
    if (passcode.length < 6) {
      const newPasscode = passcode + digit
      setPasscode(newPasscode)
      setPasscodeError('')

      // Auto-submit when 6 digits entered
      if (newPasscode.length === 6) {
        submitStepUp(newPasscode, 'passcode')
      }
    }
  }

  const handleDelete = () => {
    setPasscode(passcode.slice(0, -1))
    setPasscodeError('')
  }

  const handleBiometric = async () => {
    setIsLoading(true)
    try {
      const result = await deviceBridge.requestBiometricProof('step-up')
      if (result.success && result.proof_data) {
        await submitStepUp(result.proof_data, 'biometric')
      } else {
        setPasscodeError(result.error_message || 'Biometric authentication failed. Please use passcode.')
      }
    } catch (error) {
      console.error('Biometric authentication failed:', error)
      setPasscodeError('Biometric authentication failed. Please use passcode.')
    } finally {
      setIsLoading(false)
    }
  }

  const submitStepUp = async (proofValue: string, method: 'passcode' | 'biometric') => {
    if (!challengeReference) {
      setPasscodeError('Challenge not initialized. Please refresh the page.')
      return
    }

    setIsLoading(true)

    try {
      const deviceIdentifier = await deviceBridge.getDeviceIdentifier()

      const response = await apiClient.post<VerifyStepUpResponse>(
        `/auth/step-up/${challengeReference}/verify`,
        {
          method,
          proof_value: proofValue,
          device_id: deviceIdentifier,
        }
      )

      if (response.verified) {
        // Success - redirect to return path
        navigate(returnPath, { replace: true })
      } else {
        setPasscodeError('Verification failed. Please try again.')
        setPasscode('')
      }
    } catch (error: unknown) {
      console.error('Step-up verification failed:', error)
      
      if (error && typeof error === 'object' && 'response' in error && 
          typeof error.response === 'object' && error.response && 
          'status' in error.response && error.response.status === 401) {
        setPasscodeError('Invalid passcode. Please try again.')
      } else {
        setPasscodeError('Verification failed. Please try again.')
      }
      setPasscode('')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCancel = () => {
    navigate(returnPath, { replace: true })
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-500 to-primary-700 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-md mx-auto px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">Additional Authentication</h1>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-lg shadow-xl p-8">
            <div className="text-center mb-6">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">Verify Your Identity</h2>
              <p className="text-gray-600">
                For your security, please confirm your identity to continue
              </p>
            </div>

            {/* Passcode Display */}
            <div className="mb-6">
              <div className="flex justify-center space-x-3 mb-2">
                {[0, 1, 2, 3, 4, 5].map((i) => (
                  <div
                    key={i}
                    className={`w-12 h-14 border-2 rounded-lg flex items-center justify-center text-2xl font-semibold
                      ${passcode.length > i ? 'border-primary-600 bg-primary-50' : 'border-gray-300'}
                      ${passcodeError ? 'border-red-500 bg-red-50' : ''}`}
                  >
                    {passcode.length > i && (showPasscode ? passcode[i] : '•')}
                  </div>
                ))}
              </div>
              
              <div className="text-center">
                <button
                  type="button"
                  onClick={() => setShowPasscode(!showPasscode)}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  {showPasscode ? 'Hide' : 'Show'} passcode
                </button>
              </div>

              {passcodeError && (
                <p className="text-red-600 text-sm text-center mt-2">{passcodeError}</p>
              )}
            </div>

            {/* Numeric Keypad */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((digit) => (
                <button
                  key={digit}
                  onClick={() => handlePasscodeInput(digit.toString())}
                  disabled={isLoading || passcode.length >= 6}
                  className="h-14 text-xl font-semibold bg-gray-100 hover:bg-gray-200 active:bg-gray-300 
                    rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {digit}
                </button>
              ))}
              
              <button
                onClick={handleBiometric}
                disabled={isLoading}
                className="h-14 bg-gray-100 hover:bg-gray-200 active:bg-gray-300 rounded-lg 
                  transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                title="Use biometric"
              >
                <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 11c0 3.517-1.009 6.799-2.753 9.571m-3.44-2.04l.054-.09A13.916 13.916 0 008 11a4 4 0 118 0c0 1.017-.07 2.019-.203 3m-2.118 6.844A21.88 21.88 0 0015.171 17m3.839 1.132c.645-2.266.99-4.659.99-7.132A8 8 0 008 4.07M3 15.364c.64-1.319 1-2.8 1-4.364 0-1.457.39-2.823 1.07-4" />
                </svg>
              </button>

              <button
                onClick={() => handlePasscodeInput('0')}
                disabled={isLoading || passcode.length >= 6}
                className="h-14 text-xl font-semibold bg-gray-100 hover:bg-gray-200 active:bg-gray-300 
                  rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                0
              </button>

              <button
                onClick={handleDelete}
                disabled={isLoading || passcode.length === 0}
                className="h-14 bg-gray-100 hover:bg-gray-200 active:bg-gray-300 rounded-lg 
                  transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                <svg className="w-6 h-6 text-gray-700" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2M3 12l6.414 6.414a2 2 0 001.414.586H19a2 2 0 002-2V7a2 2 0 00-2-2h-8.172a2 2 0 00-1.414.586L3 12z" />
                </svg>
              </button>
            </div>

            {/* Cancel Button */}
            <button
              onClick={handleCancel}
              disabled={isLoading}
              className="w-full py-3 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-lg 
                transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Cancel
            </button>

            {isLoading && (
              <div className="mt-4 text-center">
                <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default StepUpPage
