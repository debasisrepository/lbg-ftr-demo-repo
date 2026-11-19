/**
 * Inactivity guard component
 * - Monitors user activity
 * - Shows warning before session timeout
 * - Provides extend/sign-out options
 */

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../lib/auth-context'

interface InactivityGuardProps {
  children: React.ReactNode
  inactivityTimeoutMs?: number
  warningTimeMs?: number
}

export function InactivityGuard({
  children,
  inactivityTimeoutMs = 300000, // 5 minutes default (from config)
  warningTimeMs = 240000, // 4 minutes default (from config)
}: InactivityGuardProps) {
  const { isAuthenticated, logout } = useAuth()
  const [showWarning, setShowWarning] = useState(false)
  const [remainingSeconds, setRemainingSeconds] = useState(0)

  const lastActivityRef = useRef<number>(Date.now())
  const warningTimerRef = useRef<NodeJS.Timeout>()
  const logoutTimerRef = useRef<NodeJS.Timeout>()
  const countdownTimerRef = useRef<NodeJS.Timeout>()

  // Reset activity timestamp
  const resetActivity = () => {
    if (!isAuthenticated) return

    lastActivityRef.current = Date.now()
    setShowWarning(false)

    // Clear existing timers
    if (warningTimerRef.current) clearTimeout(warningTimerRef.current)
    if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current)
    if (countdownTimerRef.current) clearInterval(countdownTimerRef.current)

    // Set warning timer
    warningTimerRef.current = setTimeout(() => {
      setShowWarning(true)
      const timeoutIn = inactivityTimeoutMs - warningTimeMs
      setRemainingSeconds(Math.floor(timeoutIn / 1000))

      // Start countdown
      countdownTimerRef.current = setInterval(() => {
        setRemainingSeconds((prev) => {
          if (prev <= 1) {
            if (countdownTimerRef.current) clearInterval(countdownTimerRef.current)
            return 0
          }
          return prev - 1
        })
      }, 1000)
    }, warningTimeMs)

    // Set logout timer
    logoutTimerRef.current = setTimeout(() => {
      logout()
    }, inactivityTimeoutMs)
  }

  // Track user activity
  useEffect(() => {
    if (!isAuthenticated) return

    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart']

    const handleActivity = () => {
      const now = Date.now()
      // Only reset if more than 1 second has passed (debounce)
      if (now - lastActivityRef.current > 1000) {
        resetActivity()
      }
    }

    // Add event listeners
    activityEvents.forEach((event) => {
      window.addEventListener(event, handleActivity)
    })

    // Initialize timers
    resetActivity()

    // Cleanup
    return () => {
      activityEvents.forEach((event) => {
        window.removeEventListener(event, handleActivity)
      })
      if (warningTimerRef.current) clearTimeout(warningTimerRef.current)
      if (logoutTimerRef.current) clearTimeout(logoutTimerRef.current)
      if (countdownTimerRef.current) clearInterval(countdownTimerRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  const handleExtendSession = () => {
    resetActivity()
  }

  const handleSignOut = () => {
    logout()
  }

  if (!isAuthenticated) {
    return <>{children}</>
  }

  return (
    <>
      {children}
      {showWarning && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Session Timeout Warning
            </h2>
            <p className="text-gray-700 mb-4">
              Your session will expire in{' '}
              <span className="font-semibold text-red-600">{remainingSeconds}</span>{' '}
              seconds due to inactivity.
            </p>
            <p className="text-gray-600 mb-6 text-sm">
              Would you like to extend your session or sign out?
            </p>
            <div className="flex gap-3">
              <button
                onClick={handleExtendSession}
                className="flex-1 bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                Extend Session
              </button>
              <button
                onClick={handleSignOut}
                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-400"
              >
                Sign Out
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
