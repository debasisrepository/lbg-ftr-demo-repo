/**
 * Scam Report Page
 * Wireframe 06 - J-01 step 6: Report a scam concern (FR-006)
 * - Reason list from static scam-claim-reasons.ts
 * - Optional description
 * - Claim reference and next steps
 */

import { useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { useCreateScamClaim } from '../features/support/useCreateScamClaim'
import { SCAM_CLAIM_REASONS } from '../lib/scam-claim-reasons'
import { formatMinor } from '../lib/money'
import { ReimbursementTimeline } from '../components/support/ReimbursementTimeline'

interface LocationState {
  payment_order_id?: string
  customer_payment_ref?: string
  amount_minor?: number
  payee_name?: string
}

export default function ScamReportPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as LocationState | null

  const { createScamClaim, loading } = useCreateScamClaim()

  const [selectedReason, setSelectedReason] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [submitted, setSubmitted] = useState(false)
  const [claimReference, setClaimReference] = useState<string | null>(null)
  const [supportCaseRef, setSupportCaseRef] = useState<string | null>(null)

  const paymentOrderId = state?.payment_order_id
  const customerPaymentRef = state?.customer_payment_ref
  const amountMinor = state?.amount_minor
  const payeeName = state?.payee_name

  const handleSubmit = async () => {
    if (!selectedReason) return

    const result = await createScamClaim({
      payment_order_id: paymentOrderId,
      claim_reason_code: selectedReason,
      notes: description || undefined,
    })

    if (result) {
      setClaimReference(result.claim_reference)
      setSupportCaseRef(result.support_case_reference || null)
      setSubmitted(true)
    }
  }

  if (submitted && claimReference) {
    return (
      <div className="min-h-screen bg-gray-100 flex flex-col">
        {/* Status Bar */}
        <div className="h-11 bg-white flex items-center px-6 font-semibold text-sm">
          9:41
        </div>

        {/* Content */}
        <div className="flex-1 bg-white px-6 py-8 flex flex-col">
          {/* Success Icon */}
          <div
            className="w-18 h-18 border-[3px] border-black rounded-full flex items-center justify-center my-6"
            aria-hidden="true"
          >
            <svg
              viewBox="0 0 24 24"
              className="w-10 h-10 stroke-black fill-none stroke-[3]"
            >
              <path d="M4 12l5 5 11-11" strokeLinecap="square" />
            </svg>
          </div>

          <h2 className="text-[28px] leading-9 font-semibold mb-3">
            Scam report received
          </h2>

          <p className="text-base leading-6 text-gray-700 mb-6">
            Thank you for reporting this. We&apos;ll investigate and contact you
            within 24 hours.
          </p>

          {/* Claim Reference */}
          <div className="border border-gray-400 bg-gray-100 px-4 py-3 mb-4 text-sm leading-5 flex justify-between">
            <span>Claim reference</span>
            <span className="font-semibold">{claimReference}</span>
          </div>

          {supportCaseRef && (
            <div className="border border-gray-400 bg-gray-100 px-4 py-3 mb-4 text-sm leading-5 flex justify-between">
              <span>Support case</span>
              <span className="font-semibold">{supportCaseRef}</span>
            </div>
          )}

          {/* Next Steps */}
          <div className="border border-gray-400 border-l-4 border-l-black bg-gray-100 px-4 py-3 mb-4 text-sm leading-5">
            <p className="font-semibold text-base leading-6 mb-1">Next steps</p>
            <ul className="list-disc list-inside space-y-1">
              <li>Save your claim reference for future contact</li>
              <li>We&apos;ll contact you within 24 hours</li>
              <li>
                If you need immediate help: 0345 300 0000 (24/7 fraud helpline)
              </li>
            </ul>
          </div>

          {/* Reimbursement Timeline */}
          <ReimbursementTimeline claimType={selectedReason} />

          <div className="flex-1" />

          <button
            onClick={() => navigate('/accounts')}
            className="w-full min-h-[52px] px-4 border-2 border-black bg-black text-white font-semibold text-base hover:bg-gray-900 mt-3"
          >
            Back to accounts
          </button>
        </div>
      </div>
    )
  }

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
          Tell us what happened
        </h2>
        <p className="text-base leading-6 text-gray-700 mb-6">
          If you think you&apos;ve been tricked into paying, tell us now. The
          sooner we know, the more we can do.
        </p>

        {/* Payment Reference */}
        {customerPaymentRef && (
          <div className="border border-gray-400 bg-gray-100 px-4 py-3 mb-4 text-sm leading-5 flex justify-between">
            <span>Payment reference</span>
            <span className="font-semibold">{customerPaymentRef}</span>
          </div>
        )}

        {/* Payment Details */}
        {amountMinor && payeeName && (
          <div className="border border-gray-400 bg-gray-100 px-4 py-3 mb-4 text-sm leading-5 flex justify-between">
            <span>Payment</span>
            <span className="font-semibold">
              {formatMinor(amountMinor)} to {payeeName}
            </span>
          </div>
        )}

        {/* Reason Selection */}
        <div className="mb-6">
          <label className="block text-sm leading-5 font-semibold mb-2">
            What type of scam was this?
          </label>
          <div className="space-y-2">
            {SCAM_CLAIM_REASONS.map((reason) => (
              <label
                key={reason.code}
                className="flex items-center space-x-2 cursor-pointer"
              >
                <input
                  type="radio"
                  name="scam-reason"
                  value={reason.code}
                  checked={selectedReason === reason.code}
                  onChange={(e) => setSelectedReason(e.target.value)}
                  className="w-4 h-4"
                />
                <span className="text-sm">{reason.label}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Description */}
        <div className="mb-6">
          <label
            htmlFor="description"
            className="block text-sm leading-5 font-semibold mb-2"
          >
            Tell us more (optional)
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            maxLength={500}
            placeholder="Any additional details that might help us investigate..."
            className="w-full border border-gray-400 bg-gray-100 px-4 py-3 text-base resize-none"
          />
          <p className="text-xs text-gray-600 mt-1">
            {description.length} / 500 characters
          </p>
        </div>

        <div className="flex-1" />

        {/* Submit Button */}
        <button
          onClick={handleSubmit}
          disabled={!selectedReason || loading}
          className={`w-full min-h-[52px] px-4 border-2 font-semibold text-base mt-3 ${
            !selectedReason || loading
              ? 'border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'border-black bg-black text-white hover:bg-gray-900'
          }`}
        >
          {loading ? 'Submitting...' : 'Report a scam'}
        </button>

        <button
          onClick={() => navigate('/accounts')}
          disabled={loading}
          className="w-full min-h-[52px] px-4 border-2 border-black bg-white text-black font-semibold text-base hover:bg-gray-50 mt-3"
        >
          Back to accounts
        </button>
      </div>
    </div>
  )
}
