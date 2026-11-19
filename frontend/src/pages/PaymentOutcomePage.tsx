/**
 * Payment Outcome Page
 * Wireframe 06 - J-01 step 6: Payment sent (FR-006)
 * - Sent/pending/failed status with payment reference
 * - "Do not retry" guidance for pending
 * - Expected arrival
 * - "Report a scam concern" route to ScamReportPage
 */

import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePaymentFlow } from '../features/payments/PaymentFlowProvider'
import { usePaymentStatus } from '../features/payments/usePaymentStatus'
import { formatMinor } from '../lib/money'

export default function PaymentOutcomePage() {
  const navigate = useNavigate()
  const { paymentOrderId, resetFlow } = usePaymentFlow()

  const { status, loading } = usePaymentStatus(paymentOrderId, true)

  useEffect(() => {
    if (!paymentOrderId) {
      navigate('/accounts')
    }
  }, [paymentOrderId, navigate])

  const handleBackToAccounts = () => {
    resetFlow()
    navigate('/accounts')
  }

  const handleMakeAnother = () => {
    resetFlow()
    navigate('/pay')
  }

  const handleReportScam = () => {
    navigate('/payment/scam-report', {
      state: {
        payment_order_id: paymentOrderId,
        customer_payment_ref: status?.customer_payment_ref,
        amount_minor: status?.amount_minor,
        payee_name: status?.payee_name,
      },
    })
  }

  if (loading || !status) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <p className="text-sm">Loading payment status...</p>
      </div>
    )
  }

  const isSent = status.normalized_status === 'sent'
  const isPending = status.normalized_status === 'pending'
  const isFailed = status.normalized_status === 'failed'

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col">
      {/* Status Bar */}
      <div className="h-11 bg-white flex items-center px-6 font-semibold text-sm">
        9:41
      </div>

      {/* Content */}
      <div className="flex-1 bg-white px-6 py-8 flex flex-col">
        {/* Status Icon */}
        <div
          className={`w-18 h-18 border-[3px] rounded-full flex items-center justify-center my-6 ${
            isSent
              ? 'border-black'
              : isFailed
              ? 'border-red-700'
              : 'border-black'
          }`}
          aria-hidden="true"
        >
          {isSent && (
            <svg
              viewBox="0 0 24 24"
              className="w-10 h-10 stroke-black fill-none stroke-[3]"
            >
              <path d="M4 12l5 5 11-11" strokeLinecap="square" />
            </svg>
          )}
          {isPending && (
            <svg
              viewBox="0 0 24 24"
              className="w-10 h-10 stroke-black fill-none stroke-[3]"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7v5l3 2" />
            </svg>
          )}
          {isFailed && (
            <svg
              viewBox="0 0 24 24"
              className="w-10 h-10 stroke-red-700 fill-none stroke-[3]"
            >
              <path d="M6 6l12 12M18 6L6 18" strokeLinecap="square" />
            </svg>
          )}
        </div>

        {/* Status Tag */}
        <span
          className={`inline-block self-start border-2 px-3 py-1 text-sm leading-5 font-semibold mb-3 ${
            isSent
              ? 'border-black text-black'
              : isFailed
              ? 'border-red-700 text-red-700'
              : 'border-black text-black'
          }`}
        >
          {isSent && 'Sent'}
          {isPending && 'Pending'}
          {isFailed && 'Failed'}
        </span>

        {/* Title */}
        <h2 className="text-[28px] leading-9 font-semibold mb-3">
          {isSent && 'Payment sent'}
          {isPending && 'Payment pending'}
          {isFailed && 'Payment not sent'}
        </h2>

        {/* Body Text */}
        {isSent && (
          <p className="text-base leading-6 text-gray-700 mb-6">
            {formatMinor(status.amount_minor)} is on its way to {status.payee_name}.{' '}
            {status.expected_arrival_text ||
              'It should arrive within 2 hours.'}
          </p>
        )}

        {isPending && (
          <p className="text-base leading-6 text-gray-700 mb-6">
            We&apos;re waiting for confirmation that {formatMinor(status.amount_minor)}{' '}
            to {status.payee_name} has gone through. Don&apos;t make this payment
            again. We&apos;ll tell you as soon as we know.
          </p>
        )}

        {isFailed && (
          <div
            className="border border-gray-400 border-l-4 border-l-red-700 bg-red-50 px-4 py-3 mb-4 text-sm leading-5"
            role="alert"
          >
            <p className="font-semibold text-base leading-6 mb-1">
              Error: we couldn&apos;t send this payment
            </p>
            <p>
              No money has left your account. You can try again, or contact us if
              you need help.
            </p>
          </div>
        )}

        {/* Payment Reference */}
        <div className="border border-gray-400 bg-gray-100 px-4 py-3 mb-4 text-sm leading-5 flex justify-between">
          <span>Payment reference:</span>
          <span className="font-semibold">
            {status.customer_payment_ref || 'N/A'}
          </span>
        </div>

        <div className="flex-1" />

        {/* Action Buttons */}
        {isSent && (
          <>
            <button
              onClick={handleBackToAccounts}
              className="w-full min-h-[52px] px-4 border-2 border-black bg-black text-white font-semibold text-base hover:bg-gray-900 mt-3"
            >
              Back to accounts
            </button>
            <button
              onClick={handleMakeAnother}
              className="w-full min-h-[52px] px-4 border-2 border-black bg-white text-black font-semibold text-base hover:bg-gray-50 mt-3"
            >
              Make another payment
            </button>
            <button
              onClick={handleReportScam}
              className="inline-block text-black underline text-sm min-h-11 leading-[44px] mt-1"
            >
              Report a scam concern
            </button>
          </>
        )}

        {isPending && (
          <>
            <button
              onClick={handleBackToAccounts}
              className="w-full min-h-[52px] px-4 border-2 border-black bg-black text-white font-semibold text-base hover:bg-gray-900 mt-3"
            >
              Back to accounts
            </button>
            <button
              onClick={() => window.location.reload()}
              className="w-full min-h-[52px] px-4 border-2 border-black bg-white text-black font-semibold text-base hover:bg-gray-50 mt-3"
            >
              Check status
            </button>
          </>
        )}

        {isFailed && (
          <>
            <button
              onClick={() => navigate(-2)}
              className="w-full min-h-[52px] px-4 border-2 border-black bg-black text-white font-semibold text-base hover:bg-gray-900 mt-3"
            >
              Try again
            </button>
            <button
              onClick={handleBackToAccounts}
              className="w-full min-h-[52px] px-4 border-2 border-black bg-white text-black font-semibold text-base hover:bg-gray-50 mt-3"
            >
              Back to accounts
            </button>
            <button
              onClick={handleReportScam}
              className="inline-block text-black underline text-sm min-h-11 leading-[44px] mt-1"
            >
              I think this is a scam
            </button>
          </>
        )}
      </div>
    </div>
  )
}
