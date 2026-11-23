import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect } from 'react';

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

export function PaymentOutcomePage() {
  const location = useLocation();
  const navigate = useNavigate();
  const payment = location.state?.payment as PaymentReviewResponse | undefined;
  const wasStopped = location.state?.wasStopped as boolean | undefined;

  useEffect(() => {
    if (!payment) {
      navigate('/accounts');
      return;
    }

    // Redirect to specific outcome pages based on customer_visible_status
    if (!wasStopped && payment.customer_visible_status) {
      const paymentId = payment.payment_id;
      
      if (payment.customer_visible_status === 'Sent') {
        navigate(`/payment-sent/${paymentId}`, { state: { payment }, replace: true });
      } else if (payment.customer_visible_status === 'Failed') {
        navigate(`/payment-failed/${paymentId}`, { state: { payment }, replace: true });
      } else if (payment.customer_visible_status === 'Pending') {
        navigate('/payment-pending', { state: { payment }, replace: true });
      }
    }
  }, [payment, wasStopped, navigate]);

  if (!payment) {
    return null;
  }

  const formatAmount = (amountMinor: number): string => {
    return `£${(amountMinor / 100).toFixed(2)}`;
  };

  // This page now only shows the "stopped" state
  // Other states redirect to dedicated pages

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
        <span>9:41</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        {/* Stopped state */}
        <h1 className="text-[28px] leading-tight font-bold text-[#002563] m-0" tabIndex={-1}>
          Payment not sent
        </h1>

        <div className="flex gap-3 p-4 rounded-lg border-l-4 border-[#002563] bg-[#F2FAFF]" role="status">
          <svg className="w-6 h-6 flex-shrink-0 text-[#0074CD]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 11v6M12 7.5v.5" />
          </svg>
          <div className="text-[#002563]">
            <strong className="block font-bold">No money was sent</strong>
            <span>You stopped this payment, so it was not sent and your balance has not changed.</span>
          </div>
        </div>

        <dl className="m-0 border border-[#767676] rounded-lg bg-white">
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">To</dt>
            <dd className="m-0 font-bold text-black text-right">
              {payment.payee.payee_name}
            </dd>
          </div>
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">Amount</dt>
            <dd className="m-0 font-bold text-black text-right">
              {formatAmount(payment.amount_minor)}
            </dd>
          </div>
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">Payment reference</dt>
            <dd className="m-0 font-bold text-black text-right">
              {payment.payment_reference}
            </dd>
          </div>
          <div className="flex justify-between gap-3 p-4">
            <dt className="text-sm text-[#4F5155]">Status</dt>
            <dd className="m-0 font-bold text-black text-right">Not sent</dd>
          </div>
        </dl>

        <p className="text-sm text-[#4F5155] m-0">
          A stopped warned payment never shows Sent, Pending or Failed, because it was never submitted.
        </p>

        {/* Action buttons */}
        <button
          type="button"
          onClick={() => navigate('/accounts')}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg"
        >
          Back to accounts
        </button>

        <button
          type="button"
          onClick={() => navigate('/payees')}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-[#0074CD] bg-white border-2 border-[#0074CD] rounded-lg"
        >
          Make another payment
        </button>
      </div>
    </div>
  );
}
