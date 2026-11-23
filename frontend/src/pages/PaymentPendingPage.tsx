import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { PendingBadge } from '../components/payments/PendingBadge';

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
  hold_latest_decision_at?: string;
  expected_arrival_time?: string;
  as_of_timestamp?: string;
  created_at: string;
  updated_at: string;
}

export function PaymentPendingPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const payment = location.state?.payment as PaymentReviewResponse | undefined;
  const [isCheckingStatus, setIsCheckingStatus] = useState(false);
  const [currentPayment, setCurrentPayment] = useState(payment);

  useEffect(() => {
    if (!payment || payment.customer_visible_status !== 'Pending') {
      navigate('/accounts');
    }
  }, [payment, navigate]);

  if (!currentPayment) {
    return null;
  }

  const formatAmount = (amountMinor: number): string => {
    return `£${(amountMinor / 100).toFixed(2)}`;
  };

  const formatDateTime = (isoString: string): string => {
    const date = new Date(isoString);
    const today = new Date();
    const isToday = date.toDateString() === today.toDateString();
    
    if (isToday) {
      return `Today at ${date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })}`;
    }
    
    return date.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
  };

  const handleCheckStatus = async () => {
    setIsCheckingStatus(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL ?? '/api'}/v1/payments/${currentPayment.payment_id}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to check payment status');
      }

      const updatedPayment: PaymentReviewResponse = await response.json();
      setCurrentPayment(updatedPayment);
      
      // If status changed from Pending, navigate to appropriate page
      if (updatedPayment.customer_visible_status === 'Sent') {
        navigate('/payment-outcome', { state: { payment: updatedPayment } });
      } else if (updatedPayment.customer_visible_status === 'Failed') {
        navigate('/payment-outcome', { state: { payment: updatedPayment } });
      }

    } catch (err) {
      console.error('Failed to check status:', err);
    } finally {
      setIsCheckingStatus(false);
    }
  };

  const isHeld = currentPayment.current_state === 'held_for_review';
  const title = isHeld ? "We're checking this payment" : "Payment pending";
  const doNotResubmitMessage = isHeld
    ? "We are making some extra checks to keep your money safe. You do not need to do anything. Sending it again will not make it faster."
    : "We are still waiting for confirmation. If you send it again you could pay twice. Use Check status to see the latest.";

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
        <span>9:41</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        <h1 className="text-[28px] leading-tight font-bold text-[#002563] m-0" tabIndex={-1}>
          {title}
        </h1>

        {/* Pending badge */}
        <PendingBadge />

        {/* Do not resubmit message */}
        {currentPayment.do_not_resubmit && (
          <div className="flex gap-3 p-3 rounded-lg border-[3px] border-[#002563] bg-[#F2FAFF]">
            <svg
              className="w-6 h-6 flex-shrink-0 text-[#002563]"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 7v6M12 16.5v.5" />
            </svg>
            <div className="text-black">
              <strong className="block font-bold text-lg">Don't send this payment again</strong>
              <span>{doNotResubmitMessage}</span>
            </div>
          </div>
        )}

        {/* Payment details */}
        <dl className="m-0 border border-[#767676] rounded-lg bg-white">
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">To</dt>
            <dd className="m-0 font-bold text-black text-right">
              {currentPayment.payee.payee_name}
            </dd>
          </div>
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">Amount</dt>
            <dd className="m-0 font-bold text-black text-right">
              {formatAmount(currentPayment.amount_minor)}
            </dd>
          </div>
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">Payment reference</dt>
            <dd className="m-0 font-bold text-black text-right">
              {currentPayment.payment_reference}
            </dd>
          </div>
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">Status</dt>
            <dd className="m-0 font-bold text-black text-right">Pending</dd>
          </div>
          
          {/* Show hold decision date when held */}
          {isHeld && currentPayment.hold_latest_decision_at && (
            <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
              <dt className="text-sm text-[#4F5155]">We will decide by</dt>
              <dd className="m-0 font-bold text-black text-right">
                {formatDateTime(currentPayment.hold_latest_decision_at)}
              </dd>
            </div>
          )}
          
          {/* Show status as-of time when available */}
          {currentPayment.as_of_timestamp && (
            <div className="flex justify-between gap-3 p-4">
              <dt className="text-sm text-[#4F5155]">Status as of</dt>
              <dd className="m-0 font-bold text-black text-right">
                {formatDateTime(currentPayment.as_of_timestamp)}
              </dd>
            </div>
          )}
        </dl>

        {/* Check status button */}
        <button
          type="button"
          onClick={handleCheckStatus}
          disabled={isCheckingStatus}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg disabled:opacity-50"
        >
          {isCheckingStatus ? 'Checking...' : 'Check status'}
        </button>

        {/* Back to accounts */}
        <button
          type="button"
          onClick={() => navigate('/accounts')}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-[#0074CD] bg-white border-2 border-[#0074CD] rounded-lg"
        >
          Back to accounts
        </button>

        {/* Live region for status updates */}
        <p className="p-2 rounded-lg bg-[#F2FAFF] text-[#002563] text-sm" role="status" aria-live="polite">
          We will update this screen when the status changes.
        </p>

        {/* Hint about expected arrival time */}
        {!currentPayment.expected_arrival_time && (
          <p className="text-sm text-[#4F5155] m-0">
            No expected arrival time is shown, because the payment status flow has not supplied one. The app never guesses.
          </p>
        )}
      </div>
    </div>
  );
}
