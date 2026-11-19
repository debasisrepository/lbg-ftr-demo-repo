/**
 * Review Approve Page
 * Wireframe 05 - J-01 step 5: Approve with Face ID (FR-005)
 * - Dynamic link values display
 * - Passcode or biometric approval
 * - RiskFrictionPanel for warn/challenge
 * - Held/failed treatment for hold/block
 */

import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { usePaymentFlow } from '../features/payments/PaymentFlowProvider'
import { useApprovePayment } from '../features/payments/useApprovePayment'
import { useSubmitPayment } from '../features/payments/useSubmitPayment'
import { RiskFrictionPanel } from '../components/payments/RiskFrictionPanel'
import { useRiskResponse } from '../features/payments/useRiskResponse'
import { formatMinor } from '../lib/money'
import { deviceBridge } from '../lib/device-bridge'

export default function ReviewApprovePage() {
  const navigate = useNavigate()
  const {
    preparedPayment,
    riskFriction,
    setRiskFriction,
    paymentOrderId,
    transitionTo,
  } = usePaymentFlow()

  const { approvePayment, loading: approving } = useApprovePayment()
  const { submitPayment, loading: submitting } = useSubmitPayment()
  const { respondToRisk, loading: respondingToRisk } = useRiskResponse()

  const [showFriction, setShowFriction] = useState(false)

  useEffect(() => {
    if (!preparedPayment) {
      navigate('/accounts')
      return
    }

    // Check risk decision
    if (preparedPayment.risk_decision === 'warn') {
      setRiskFriction({
        type: 'warn',
        title: 'Warning: this payment looks unusual',
        message:
          "Fraudsters can pretend to be landlords or companies you know. Only continue if you've checked these details with the payee using a number you trust.",
      })
      setShowFriction(true)
    } else if (preparedPayment.risk_decision === 'challenge') {
      setRiskFriction({
        type: 'challenge',
        title: 'Additional information needed',
        message: 'To help protect you, tell us what this payment is for.',
        requiresPurpose: true,
      })
      setShowFriction(true)
    } else if (preparedPayment.risk_decision === 'hold') {
      setRiskFriction({
        type: 'hold',
        title: 'Payment held for review',
        message:
          "We're reviewing this payment for your safety. You'll be notified within 24 hours.",
      })
      setShowFriction(true)
    } else if (preparedPayment.risk_decision === 'block') {
      setRiskFriction({
        type: 'block',
        title: 'Payment blocked',
        message:
          'This payment cannot be sent right now. Contact us for help: 0345 300 0000 (24/7 fraud helpline).',
      })
      setShowFriction(true)
    }
  }, [preparedPayment, navigate, setRiskFriction])

  const handleRiskAcknowledge = async () => {
    if (!paymentOrderId) return

    const result = await respondToRisk(paymentOrderId, {
      response_type: 'acknowledged',
    })

    if (result && result.can_proceed) {
      setShowFriction(false)
      setRiskFriction(null)
    }
  }

  const handleProvidePurpose = async (purpose: string) => {
    if (!paymentOrderId) return

    const result = await respondToRisk(paymentOrderId, {
      response_type: 'purpose_provided',
      payment_purpose: purpose,
    })

    if (result && result.can_proceed) {
      setShowFriction(false)
      setRiskFriction(null)
    }
  }

  const handleCancel = async () => {
    if (!paymentOrderId) return

    await respondToRisk(paymentOrderId, {
      response_type: 'cancelled',
    })

    navigate('/accounts')
  }

  const handleApprove = async () => {
    if (!paymentOrderId) return

    transitionTo('approving')

    // Try biometric first
    const biometricAvailable = await deviceBridge.isBiometricAvailable()
    let deviceAttestation: string | undefined

    if (biometricAvailable) {
      const proofResult = await deviceBridge.requestBiometricProof(
        preparedPayment?.dynamic_link_digest || ''
      )
      if (proofResult.success && proofResult.proof_data) {
        deviceAttestation = proofResult.proof_data
      }
    }

    // Approve payment
    const approvalResult = await approvePayment(paymentOrderId, {
      device_attestation: deviceAttestation,
    })

    if (!approvalResult) {
      transitionTo('prepared')
      return
    }

    // Submit payment
    transitionTo('submitting')
    const submitResult = await submitPayment(paymentOrderId)

    if (submitResult) {
      transitionTo('outcome')
      navigate('/payment/outcome')
    } else {
      transitionTo('prepared')
    }
  }

  if (!preparedPayment) {
    return null
  }

  const isProcessing = approving || submitting || respondingToRisk

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
        {showFriction && riskFriction ? (
          <>
            <h2 className="text-[28px] leading-9 font-semibold mt-4 mb-1">
              {riskFriction.type === 'warn' ? 'Check before you pay' : 'Payment review'}
            </h2>
            <p className="text-sm leading-5 text-gray-600 mb-6">
              {formatMinor(preparedPayment.amount_minor)} to{' '}
              {preparedPayment.payee_name}
            </p>

            <RiskFrictionPanel
              type={riskFriction.type}
              title={riskFriction.title}
              message={riskFriction.message}
              requiresPurpose={riskFriction.requiresPurpose}
              onAcknowledge={handleRiskAcknowledge}
              onCancel={handleCancel}
              onProvidePurpose={handleProvidePurpose}
            />
          </>
        ) : (
          <>
            <h2 className="text-[28px] leading-9 font-semibold mt-4 mb-1">
              Approve payment
            </h2>
            <p className="text-sm leading-5 text-gray-600 mb-6">
              Check these details. Once sent, a payment can&apos;t be taken back.
            </p>

            {/* Payment Details Review */}
            <div className="border border-gray-400 mb-4" aria-label="Payment details being approved">
              <div className="flex justify-between px-4 py-3 border-b border-gray-300 text-sm leading-5">
                <span className="text-gray-600">From</span>
                <span className="font-semibold text-base">
                  {preparedPayment.source_account_name}
                </span>
              </div>
              <div className="flex justify-between px-4 py-3 border-b border-gray-300 text-sm leading-5">
                <span className="text-gray-600">To</span>
                <span className="font-semibold text-base">
                  {preparedPayment.payee_name}
                </span>
              </div>
              <div className="flex justify-between px-4 py-3 border-b border-gray-300 text-sm leading-5">
                <span className="text-gray-600">Amount</span>
                <span className="font-semibold text-base">
                  {formatMinor(preparedPayment.amount_minor)}
                </span>
              </div>
              {preparedPayment.payment_reference && (
                <div className="flex justify-between px-4 py-3 text-sm leading-5">
                  <span className="text-gray-600">Reference</span>
                  <span className="font-semibold text-base">
                    {preparedPayment.payment_reference}
                  </span>
                </div>
              )}
            </div>

            {/* Face ID Panel */}
            <div className="border-2 border-black px-6 py-6 flex flex-col items-center gap-3 text-center mt-2">
              <svg
                viewBox="0 0 24 24"
                className="w-12 h-12 stroke-black fill-none stroke-2"
                aria-hidden="true"
              >
                <path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4M9 10v2M15 10v2M9 16c1.5 1 4.5 1 6 0" />
              </svg>
              <p className="font-semibold text-lg">
                Approve {formatMinor(preparedPayment.amount_minor)} to{' '}
                {preparedPayment.payee_name} with Face ID
              </p>
            </div>

            <div className="flex-1" />

            {/* Action Buttons */}
            <button
              onClick={handleApprove}
              disabled={isProcessing}
              className={`w-full min-h-[52px] px-4 border-2 font-semibold text-base mt-3 ${
                isProcessing
                  ? 'border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'border-black bg-black text-white hover:bg-gray-900'
              }`}
            >
              {isProcessing ? 'Processing...' : 'Approve with Face ID'}
            </button>

            <button
              onClick={() => navigate('/accounts')}
              disabled={isProcessing}
              className="w-full min-h-[52px] px-4 border-2 border-black bg-white text-black font-semibold text-base mt-3 hover:bg-gray-50"
            >
              Cancel
            </button>
          </>
        )}
      </div>
    </div>
  )
}
