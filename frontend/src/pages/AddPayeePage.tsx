/**
 * Add Payee Page
 * Implements FR-004: Payee Management with Confirmation of Payee
 * Wireframe: wireframe_04_j01_s04.html (states B, C, D)
 */

import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useCreatePayee } from '../features/payees/useCreatePayee'
import { CopOutcomePanel } from '../components/payees/CopOutcomePanel'
import { validateSortCode, validateAccountNumber, validatePayeeName } from '../lib/validators'
import { CopCheckOut } from '../features/payees/usePayees'

export function AddPayeePage() {
  const navigate = useNavigate()
  const { createPayee, loading } = useCreatePayee()

  const [payeeName, setPayeeName] = useState('')
  const [sortCode, setSortCode] = useState('')
  const [accountNumber, setAccountNumber] = useState('')
  const [copCheck, setCopCheck] = useState<CopCheckOut | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSortCodeChange = (value: string) => {
    // Auto-format sort code as XX-XX-XX
    const digits = value.replace(/\D/g, '')
    let formatted = digits
    if (digits.length > 2) {
      formatted = digits.slice(0, 2) + '-' + digits.slice(2)
    }
    if (digits.length > 4) {
      formatted = digits.slice(0, 2) + '-' + digits.slice(2, 4) + '-' + digits.slice(4, 6)
    }
    setSortCode(formatted)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    // Validate fields
    const nameValidation = validatePayeeName(payeeName)
    if (!nameValidation.valid) {
      setError(nameValidation.error || 'Payee name is invalid')
      return
    }

    const sortCodeValidation = validateSortCode(sortCode)
    if (!sortCodeValidation.valid) {
      setError(sortCodeValidation.error || 'Sort code is invalid')
      return
    }

    const accountNumberValidation = validateAccountNumber(accountNumber)
    if (!accountNumberValidation.valid) {
      setError(accountNumberValidation.error || 'Account number is invalid')
      return
    }

    try {
      const response = await createPayee({
        payee_name: payeeName,
        sort_code: sortCode,
        account_number: accountNumber,
        payee_type: 'personal',
      })

      setCopCheck(response.cop_check)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to add payee')
    }
  }

  const handleContinue = () => {
    navigate('/pay-and-transfer')
  }

  const handleCancel = () => {
    if (copCheck?.outcome === 'unavailable') {
      navigate('/pay-and-transfer')
    } else {
      // For mismatch/partial_match, just go back
      navigate(-1)
    }
  }

  const handleTryAgain = () => {
    setCopCheck(null)
    setError(null)
  }

  const isFormReadonly = copCheck !== null

  return (
    <div style={{ minHeight: '100vh', background: '#ffffff', display: 'flex', flexDirection: 'column' }}>
      {/* Status bar */}
      <div style={{ height: '44px', flexShrink: 0, display: 'flex', alignItems: 'center', padding: '0 24px', fontSize: '14px', fontWeight: 600 }}>
        9:41
      </div>

      {/* Top bar */}
      <div style={{ minHeight: '48px', flexShrink: 0, display: 'flex', alignItems: 'center', padding: '0 8px' }}>
        <button
          onClick={() => navigate(-1)}
          style={{ width: '44px', height: '44px', border: 0, background: 'transparent', cursor: 'pointer' }}
          aria-label="Back"
        >
          <svg viewBox="0 0 24 24" style={{ width: '24px', height: '24px', stroke: '#161616', fill: 'none', strokeWidth: 2 }}>
            <path d="M19 12H5M11 5l-7 7 7 7" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: '1 0 auto', padding: '8px 24px 24px', display: 'flex', flexDirection: 'column' }}>
        <h2 style={{ margin: '16px 0 24px', fontSize: '28px', lineHeight: '36px', fontWeight: 600 }}>
          Add a new payee
        </h2>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '16px' }}>
            <label
              htmlFor="payee-name"
              style={{ display: 'block', fontSize: '14px', lineHeight: '20px', fontWeight: 600, marginBottom: '8px' }}
            >
              Payee name
            </label>
            <input
              id="payee-name"
              type="text"
              value={payeeName}
              onChange={(e) => setPayeeName(e.target.value)}
              readOnly={isFormReadonly}
              style={{
                width: '100%',
                height: '52px',
                border: '1px solid #8d8d8d',
                background: '#f4f4f4',
                padding: '0 16px',
                fontSize: '16px',
                color: '#161616',
                fontFamily: 'inherit',
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label
              htmlFor="sort-code"
              style={{ display: 'block', fontSize: '14px', lineHeight: '20px', fontWeight: 600, marginBottom: '8px' }}
            >
              Sort code
            </label>
            <input
              id="sort-code"
              type="text"
              value={sortCode}
              onChange={(e) => handleSortCodeChange(e.target.value)}
              readOnly={isFormReadonly}
              placeholder="XX-XX-XX"
              maxLength={8}
              style={{
                width: '100%',
                height: '52px',
                border: '1px solid #8d8d8d',
                background: '#f4f4f4',
                padding: '0 16px',
                fontSize: '16px',
                color: '#161616',
                fontFamily: 'inherit',
              }}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label
              htmlFor="account-number"
              style={{ display: 'block', fontSize: '14px', lineHeight: '20px', fontWeight: 600, marginBottom: '8px' }}
            >
              Account number
            </label>
            <input
              id="account-number"
              type="text"
              value={accountNumber}
              onChange={(e) => setAccountNumber(e.target.value.replace(/\D/g, '').slice(0, 8))}
              readOnly={isFormReadonly}
              placeholder="12345678"
              maxLength={8}
              style={{
                width: '100%',
                height: '52px',
                border: '1px solid #8d8d8d',
                background: '#f4f4f4',
                padding: '0 16px',
                fontSize: '16px',
                color: '#161616',
                fontFamily: 'inherit',
              }}
            />
          </div>

          {error && (
            <div
              style={{
                border: '1px solid #8d8d8d',
                borderLeft: '4px solid #c62828',
                background: '#f4f4f4',
                padding: '12px 16px',
                marginBottom: '16px',
                fontSize: '14px',
                lineHeight: '20px',
                color: '#c62828',
              }}
            >
              {error}
            </div>
          )}

          {copCheck && <CopOutcomePanel copCheck={copCheck} />}

          <div style={{ flex: '1 0 0' }} />

          {!copCheck && (
            <button
              type="submit"
              disabled={loading}
              style={{
                display: 'block',
                width: '100%',
                minHeight: '52px',
                border: '2px solid #161616',
                fontSize: '16px',
                fontWeight: 600,
                fontFamily: 'inherit',
                padding: '0 16px',
                marginTop: '12px',
                background: '#161616',
                color: '#fff',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1,
              }}
            >
              {loading ? 'Checking...' : 'Add payee'}
            </button>
          )}

          {copCheck && copCheck.outcome === 'match' && (
            <>
              <button
                type="button"
                onClick={handleContinue}
                style={{
                  display: 'block',
                  width: '100%',
                  minHeight: '52px',
                  border: '2px solid #161616',
                  fontSize: '16px',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  padding: '0 16px',
                  marginTop: '12px',
                  background: '#161616',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                Continue
              </button>
              <button
                type="button"
                onClick={handleTryAgain}
                style={{
                  display: 'block',
                  width: '100%',
                  minHeight: '52px',
                  border: '2px solid #161616',
                  fontSize: '16px',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  padding: '0 16px',
                  marginTop: '12px',
                  background: '#ffffff',
                  color: '#161616',
                  cursor: 'pointer',
                }}
              >
                Edit details
              </button>
            </>
          )}

          {copCheck && (copCheck.outcome === 'mismatch' || copCheck.outcome === 'partial_match') && (
            <>
              <button
                type="button"
                onClick={handleCancel}
                style={{
                  display: 'block',
                  width: '100%',
                  minHeight: '52px',
                  border: '2px solid #161616',
                  fontSize: '16px',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  padding: '0 16px',
                  marginTop: '12px',
                  background: '#161616',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                Check the details
              </button>
              <button
                type="button"
                onClick={handleCancel}
                style={{
                  display: 'block',
                  width: '100%',
                  minHeight: '52px',
                  border: '2px solid #161616',
                  fontSize: '16px',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  padding: '0 16px',
                  marginTop: '12px',
                  background: '#ffffff',
                  color: '#161616',
                  cursor: 'pointer',
                }}
              >
                Cancel
              </button>
            </>
          )}

          {copCheck && copCheck.outcome === 'unavailable' && (
            <>
              <button
                type="button"
                onClick={handleTryAgain}
                style={{
                  display: 'block',
                  width: '100%',
                  minHeight: '52px',
                  border: '2px solid #161616',
                  fontSize: '16px',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  padding: '0 16px',
                  marginTop: '12px',
                  background: '#161616',
                  color: '#fff',
                  cursor: 'pointer',
                }}
              >
                Try again
              </button>
              <button
                type="button"
                onClick={handleCancel}
                style={{
                  display: 'block',
                  width: '100%',
                  minHeight: '52px',
                  border: '2px solid #161616',
                  fontSize: '16px',
                  fontWeight: 600,
                  fontFamily: 'inherit',
                  padding: '0 16px',
                  marginTop: '12px',
                  background: '#ffffff',
                  color: '#161616',
                  cursor: 'pointer',
                }}
              >
                Back to payees
              </button>
            </>
          )}
        </form>
      </div>
    </div>
  )
}
