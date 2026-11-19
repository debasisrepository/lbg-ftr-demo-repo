/**
 * Risk Friction Panel
 * Displays risk warnings, challenges, hold, or block messages
 */

import { useState } from 'react'

export interface RiskFrictionPanelProps {
  type: 'warn' | 'challenge' | 'hold' | 'block'
  title: string
  message: string
  requiresPurpose?: boolean
  onAcknowledge?: () => void
  onCancel?: () => void
  onProvidePurpose?: (purpose: string) => void
}

const PURPOSE_OPTIONS = [
  { value: 'personal_expense', label: 'Personal expense' },
  { value: 'business_payment', label: 'Business payment' },
  { value: 'bill_payment', label: 'Bill or utility payment' },
  { value: 'rent_mortgage', label: 'Rent or mortgage' },
  { value: 'gift', label: 'Gift to family or friend' },
  { value: 'purchase', label: 'Purchase of goods or services' },
  { value: 'other', label: 'Other' },
]

export function RiskFrictionPanel({
  type,
  title,
  message,
  requiresPurpose = false,
  onAcknowledge,
  onCancel,
  onProvidePurpose,
}: RiskFrictionPanelProps) {
  const [selectedPurpose, setSelectedPurpose] = useState<string>('')

  const isWarn = type === 'warn'
  const isChallenge = type === 'challenge'
  const isHold = type === 'hold'
  const isBlock = type === 'block'

  const handleContinue = () => {
    if (requiresPurpose && onProvidePurpose && selectedPurpose) {
      onProvidePurpose(selectedPurpose)
    } else if (onAcknowledge) {
      onAcknowledge()
    }
  }

  return (
    <div className="space-y-4">
      {/* Warning/Error Banner */}
      <div
        className={`border-l-4 border p-3 ${
          isWarn || isChallenge
            ? 'border-l-red-700 bg-red-50'
            : isHold
            ? 'border-l-yellow-600 bg-yellow-50'
            : 'border-l-red-700 bg-red-50'
        }`}
        role="alert"
      >
        <h3 className="font-semibold text-base mb-1">{title}</h3>
        <p className="text-sm leading-5">{message}</p>
      </div>

      {/* Purpose Radio Group for Challenge */}
      {requiresPurpose && isChallenge && (
        <div className="space-y-2">
          <label className="block text-sm font-semibold">
            What is this payment for?
          </label>
          <div className="space-y-2">
            {PURPOSE_OPTIONS.map((option) => (
              <label
                key={option.value}
                className="flex items-center space-x-2 cursor-pointer"
              >
                <input
                  type="radio"
                  name="payment-purpose"
                  value={option.value}
                  checked={selectedPurpose === option.value}
                  onChange={(e) => setSelectedPurpose(e.target.value)}
                  className="w-4 h-4"
                />
                <span className="text-sm">{option.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="space-y-3">
        {!isBlock && !isHold && (
          <button
            onClick={handleContinue}
            disabled={requiresPurpose && !selectedPurpose}
            className={`w-full min-h-[52px] px-4 py-2 border-2 font-semibold text-base ${
              requiresPurpose && !selectedPurpose
                ? 'border-gray-300 bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'border-black bg-white text-black hover:bg-gray-50'
            }`}
          >
            {isWarn ? "I've checked, continue to approve" : 'Continue'}
          </button>
        )}

        {(isWarn || isChallenge) && onCancel && (
          <button
            onClick={onCancel}
            className="w-full min-h-[52px] px-4 py-2 border-2 border-black bg-black text-white font-semibold text-base hover:bg-gray-900"
          >
            Stop this payment
          </button>
        )}

        {(isHold || isBlock) && (
          <div className="text-sm text-gray-700 space-y-2">
            <p className="font-semibold">Next steps:</p>
            <ul className="list-disc list-inside space-y-1">
              {isHold && (
                <>
                  <li>We&apos;re reviewing this payment for your safety</li>
                  <li>You&apos;ll be notified within 24 hours</li>
                  <li>
                    Contact us if you need help: 0345 300 0000 (24/7 helpline)
                  </li>
                </>
              )}
              {isBlock && (
                <>
                  <li>This payment cannot be sent right now</li>
                  <li>
                    Contact us for help: 0345 300 0000 (24/7 fraud helpline)
                  </li>
                  <li>Have your payment reference ready when you call</li>
                </>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
