import { useState, useEffect, useRef } from 'react';
import { ApiError } from '../../lib/api-client';

interface PaymentReviewResponse {
  payment_id: string;
  current_state: string;
  next_action: string;
  customer_visible_status: string | null;
  status_message: string;
  is_submitted: boolean;
  do_not_resubmit: boolean;
  payment_reference: string;
  amount_minor: number;
  currency: string;
  source_account: {
    account_id: string;
    display_name: string;
    masked_account_identifier: string;
  };
  payee: {
    payee_id: string;
    payee_name: string;
    masked_account_identifier: string;
  };
  review_version: number;
  review_fingerprint: string;
  created_at: string;
  updated_at: string;
}

interface ApprovalSheetProps {
  payment: PaymentReviewResponse;
  idempotencyKey: string;
  onClose: () => void;
  onSuccess: (payment: PaymentReviewResponse) => void;
  onFailure: () => void;
}

export function ApprovalSheet({ payment, idempotencyKey, onClose, onSuccess, onFailure }: ApprovalSheetProps) {
  const [passcode, setPasscode] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const passcodeInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Focus passcode input when sheet opens
    passcodeInputRef.current?.focus();
  }, []);

  const formatAmount = (amountMinor: number): string => {
    return `£${(amountMinor / 100).toFixed(2)}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!passcode || passcode.length < 4 || passcode.length > 12) {
      setError('Enter your passcode (4-12 characters).');
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL ?? '/api'}/v1/payments/${payment.payment_id}/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`,
          'Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify({
          review_version: payment.review_version,
          review_fingerprint: payment.review_fingerprint,
          approval: {
            method: 'passcode',
            passcode: passcode,
          },
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        
        // Handle approval failure
        if (response.status === 401 || errorData.detail?.includes('approval') || errorData.detail?.includes('passcode')) {
          onFailure();
          return;
        }

        throw new ApiError(`Request failed: ${response.status}`, response.status, errorData.detail);
      }

      const updatedPayment: PaymentReviewResponse = await response.json();
      
      // Check if approval succeeded
      if (updatedPayment.current_state === 'approval_failed_or_abandoned') {
        onFailure();
      } else if (updatedPayment.current_state === 'warning_presented') {
        // Navigate to warning page instead of success
        window.location.href = '/payment-warning';
        window.history.replaceState({ payment: updatedPayment }, '', '/payment-warning');
      } else {
        onSuccess(updatedPayment);
      }

    } catch (err) {
      console.error('Failed to approve payment:', err);
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError('Failed to approve payment. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    setPasscode('');
    onClose();
  };

  return (
    <>
      {/* Overlay */}
      <div className="absolute top-0 left-0 w-full h-full bg-black bg-opacity-30" onClick={handleCancel}></div>

      {/* Sheet */}
      <div
        className="absolute bottom-0 left-0 w-full p-6 bg-white border-t-4 border-[#002563] rounded-t-2xl flex flex-col gap-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="approval-sheet-title"
        aria-describedby="approval-sheet-description"
      >
        <h2 id="approval-sheet-title" className="text-[22px] font-bold text-[#002563] m-0">
          Approve this payment
        </h2>

        <p id="approval-sheet-description" className="text-sm text-[#4F5155] m-0">
          Enter your passcode to approve {formatAmount(payment.amount_minor)} to {payment.payee.payee_name}, account ending {payment.payee.masked_account_identifier}, reference {payment.payment_reference}.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label htmlFor="passcode" className="block mb-1 text-sm font-bold text-black">
              Passcode
            </label>
            <input
              ref={passcodeInputRef}
              type="password"
              id="passcode"
              name="passcode"
              autoComplete="current-password"
              minLength={4}
              maxLength={12}
              value={passcode}
              onChange={(e) => setPasscode(e.target.value)}
              className="block w-full h-14 px-4 text-base text-black bg-white border border-[#767676] rounded-lg"
            />
          </div>

          {error && (
            <div className="flex gap-2 text-sm font-bold text-[#BE222A]" role="alert">
              <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3l10 18H2z" />
                <path d="M12 10v5M12 18v.5" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg"
          >
            {isSubmitting ? 'Approving...' : `Approve ${formatAmount(payment.amount_minor)}`}
          </button>

          <button
            type="button"
            onClick={handleCancel}
            disabled={isSubmitting}
            className="flex items-center justify-center min-h-12 px-6 font-bold text-[#0074CD] bg-white border-2 border-[#0074CD] rounded-lg"
          >
            Cancel
          </button>

          <p className="text-sm text-[#4F5155] m-0">
            The sheet clears your passcode when it closes. Cancelling leaves the payment unsent.
          </p>
        </form>
      </div>
    </>
  );
}
