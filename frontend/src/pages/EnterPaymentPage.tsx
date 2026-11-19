/**
 * Enter Payment Page
 * Wireframe 05 - J-01 step 5: Enter and approve (FR-005)
 * - Source account dropdown
 * - Amount input with GBP minor units
 * - Reference field
 * - Duplicate warning rendering
 * - Limit/balance blocking
 */

import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useAccountsOverview } from '../features/accounts/useAccountsOverview'
import { usePreparePayment } from '../features/payments/usePreparePayment'
import { usePaymentFlow } from '../features/payments/PaymentFlowProvider'
import { safeParseGbpToMinor, formatMinor } from '../lib/money'

interface LocationState {
  payee_id?: string
  payee_name?: string
  sort_code?: string
  account_number_masked?: string
}

export default function EnterPaymentPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  const { data: accountsData, loading: accountsLoading } = useAccountsOverview()
  const { preparePayment, loading: preparing } = usePreparePayment()
  const { setPreparedPayment } = usePaymentFlow()

  const [selectedAccountId, setSelectedAccountId] = useState<string>('')
  const [amountGbp, setAmountGbp] = useState<string>('')
  const [reference, setReference] = useState<string>('')
  const [limitError, setLimitError] = useState<string | null>(null)

  const payeeId = state?.payee_id || ''
  const payeeName = state?.payee_name || 'Unknown Payee'
  const sortCode = state?.sort_code || ''
  const accountNumberMasked = state?.account_number_masked || ''

  const accounts = accountsData?.accounts || []

  useEffect(() => {
    if (accounts.length > 0 && !selectedAccountId) {
      const currentAccount = accounts.find(
        (acc) => acc.account_type === 'current'
      )
      if (currentAccount) {
        setSelectedAccountId(currentAccount.bank_account_id)
      }
    }
  }, [accounts, selectedAccountId])

  const selectedAccount = accounts.find(
    (acc) => acc.bank_account_id === selectedAccountId
  )

  const availableBalance = selectedAccount?.available_balance_minor ?? 0

  const handleAmountChange = (value: string) => {
    setAmountGbp(value)
    setLimitError(null)
  }

  const handlePay = async () => {
    if (!selectedAccountId || !payeeId || !amountGbp) {
      return
    }

    const result = safeParseGbpToMinor(amountGbp)
    if (result.error) {
      setLimitError(result.error)
      return
    }

    const amountMinor = result.value!

    // Client-side balance check
    if (amountMinor > availableBalance) {
      setLimitError(
        `Error: You can pay up to ${formatMinor(availableBalance)} from this account`
      )
      return
    }

    // Generate idempotency key
    const idempotencyKey = `pay-${Date.now()}-${Math.random().toString(36).substring(2)}`

    const { data, limitError: serverLimitError } = await preparePayment({
      source_account_id: selectedAccountId,
      payee_id: payeeId,
      amount_minor: amountMinor,
      currency_code: 'GBP',
      payment_reference: reference || '',
      idempotency_key: idempotencyKey,
    })

    if (serverLimitError) {
      setLimitError(serverLimitError.message)
      return
    }

    if (data) {
      setPreparedPayment(data)
      navigate('/payment/review')
    }
  }

  const isAmountValid = amountGbp && safeParseGbpToMinor(amountGbp).value !== null

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Status Bar */}
      <div className="h-11 bg-white flex items-center px-6 font-semibold text-sm">
        9:41
      </div>

      {/* Top Bar */}
      <div className="min-h-12 bg-white flex items-center px-2">
        <button
          onClick={() => navigate(-1)}
          className="w-11 h-11 flex items-center justify-center"
          aria-label="Back"
        >
          <svg
            viewBox="0 0 24 24"
            className="w-6 h-6 stroke-current fill-none stroke-2"
            aria-hidden="true"
          >
            <path d="M19 12H5M11 5l-7 7 7 7" />
          </svg>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 bg-white px-6 py-2 flex flex-col">
        <h2 className="text-[28px] leading-9 font-semibold mt-4 mb-1">
          Pay {payeeName}
        </h2>
        <p className="text-sm leading-5 text-gray-600 mb-6">
          {sortCode} · {accountNumberMasked}
        </p>

        {accountsLoading ? (
          <p className="text-sm">Loading accounts...</p>
        ) : (
          <>
            {/* From Account */}
            <div className="mb-6">
              <label htmlFor="from-account" className="block text-sm leading-5 font-semibold mb-2">
                From
              </label>
              <div className="relative">
                <select
                  id="from-account"
                  value={selectedAccountId}
                  onChange={(e) => setSelectedAccountId(e.target.value)}
                  className="w-full min-h-[52px] border border-gray-400 bg-gray-100 px-4 text-base appearance-none pr-10"
                >
                  {accounts
                    .filter((acc) => acc.account_type !== 'credit_card')
                    .map((acc) => (
                      <option key={acc.bank_account_id} value={acc.bank_account_id}>
                        {acc.account_name || acc.account_type}{' '}
                        {formatMinor(acc.available_balance_minor ?? 0)}
                      </option>
                    ))}
                </select>
                <svg
                  viewBox="0 0 24 24"
                  className="w-5 h-5 stroke-current fill-none stroke-2 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none"
                  aria-hidden="true"
                >
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </div>
            </div>

            {/* Amount */}
            <div className="mb-6">
              <label htmlFor="amount" className="block text-sm leading-5 font-semibold mb-2">
                Amount
              </label>
              <input
                id="amount"
                type="text"
                value={amountGbp}
                onChange={(e) => handleAmountChange(e.target.value)}
                placeholder="£ 0.00"
                className={`w-full min-h-[52px] border px-4 text-base ${
                  limitError
                    ? 'border-2 border-red-700 bg-white'
                    : 'border border-gray-400 bg-gray-100'
                }`}
                aria-invalid={!!limitError}
              />
              {limitError && (
                <p className="mt-2 text-sm leading-5 text-red-700 font-semibold" role="alert">
                  {limitError}
                </p>
              )}
            </div>

            {/* Reference */}
            <div className="mb-6">
              <label htmlFor="reference" className="block text-sm leading-5 font-semibold mb-2">
                Reference (optional)
              </label>
              <input
                id="reference"
                type="text"
                value={reference}
                onChange={(e) => setReference(e.target.value)}
                maxLength={18}
                placeholder=""
                className="w-full min-h-[52px] border border-gray-400 bg-gray-100 px-4 text-base"
              />
            </div>
          </>
        )}

        <div className="flex-1" />

        {/* Pay Button */}
        <button
          onClick={handlePay}
          disabled={
            !isAmountValid ||
            !selectedAccountId ||
            !payeeId ||
            preparing ||
            !!limitError
          }
          className={`w-full min-h-[52px] px-4 border-2 font-semibold text-base mt-3 ${
            !isAmountValid ||
            !selectedAccountId ||
            !payeeId ||
            preparing ||
            !!limitError
              ? 'border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'border-black bg-black text-white hover:bg-gray-900'
          }`}
        >
          {preparing ? 'Preparing...' : `Pay ${amountGbp ? amountGbp : '£0.00'}`}
        </button>
      </div>
    </div>
  )
}
