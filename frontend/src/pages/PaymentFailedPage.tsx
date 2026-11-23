/**
 * PaymentFailedPage - shown for failed or rejected payment states (wireframe_07 C).
 * Calls GET /api/v1/payments/{payment_id} to fetch outcome details.
 * Shows Failed badge (red, icon+text), "No money was sent" message, payment reference.
 */

import { useState, useEffect } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import { apiClient } from '../lib/api-client';
import { OutcomeBadge } from '../components/payments/OutcomeBadge';
import { ReconnectingStatus } from '../components/payments/ReconnectingStatus';

interface PaymentDetailsResponse {
  payment_id: string;
  current_state: string;
  customer_visible_status: string | null;
  payment_reference: string;
  amount_minor: number;
  currency: string;
  payee_display_name: string;
  expected_arrival_time: string | null;
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
}

export function PaymentFailedPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { paymentId } = useParams<{ paymentId: string }>();
  
  const [payment, setPayment] = useState<PaymentDetailsResponse | null>(
    location.state?.payment || null
  );
  const [loading, setLoading] = useState(!location.state?.payment);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If payment not provided via state, fetch it
    if (!payment && paymentId) {
      fetchPaymentDetails(paymentId);
    }
  }, [paymentId, payment]);

  const fetchPaymentDetails = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.get<PaymentDetailsResponse>(
        `/v1/payments/${id}`
      );
      
      // Verify status is Failed
      if (data.customer_visible_status !== 'Failed') {
        // Navigate to appropriate page based on status
        if (data.customer_visible_status === 'Sent') {
          navigate(`/payment-sent/${id}`, { state: { payment: data }, replace: true });
          return;
        } else if (data.customer_visible_status === 'Pending') {
          navigate('/payment-pending', { state: { payment: data }, replace: true });
          return;
        }
      }
      
      setPayment(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payment details');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <ReconnectingStatus />;
  }

  if (error || !payment) {
    return (
      <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
        <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
          <span>9:41</span>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center gap-4 p-4">
          <p className="text-lg font-bold text-[#BE222A]">
            {error || 'Payment not found'}
          </p>
          <button
            type="button"
            onClick={() => navigate('/accounts')}
            className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg"
          >
            Back to accounts
          </button>
        </div>
      </div>
    );
  }

  const formatAmount = (amountMinor: number): string => {
    return `£${(amountMinor / 100).toFixed(2)}`;
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
        <span>9:41</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        {/* Error icon */}
        <svg
          className="w-12 h-12 text-[#BE222A]"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M8 8l8 8M16 8l-8 8" />
        </svg>

        <h1 className="text-[28px] leading-tight font-bold text-[#002563] m-0" tabIndex={-1}>
          Payment failed
        </h1>

        {/* Failed badge */}
        <OutcomeBadge status="Failed" />

        {/* Error notice */}
        <div className="flex gap-3 p-4 rounded-lg border-2 border-[#BE222A] bg-white" role="alert">
          <svg
            className="w-6 h-6 flex-shrink-0 text-[#BE222A]"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M8 8l8 8M16 8l-8 8" />
          </svg>
          <div className="text-black">
            <strong className="block font-bold">This payment was not completed</strong>
            <span>No money was sent and your balance has not changed.</span>
          </div>
        </div>

        {/* Payment details */}
        <dl className="m-0 border border-[#767676] rounded-lg bg-white">
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">To</dt>
            <dd className="m-0 font-bold text-black text-right">
              {payment.payee_display_name || payment.payee.payee_name}
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
            <dd className="m-0 font-bold text-black text-right">Failed</dd>
          </div>
        </dl>

        <p className="text-sm text-[#4F5155] m-0">
          The reference is shown so you can tell which payment this refers to. Starting a new payment makes a new journey with a new key.
        </p>

        {/* Action buttons */}
        <button
          type="button"
          onClick={() => navigate('/payees')}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg"
        >
          Start a new payment
        </button>

        <button
          type="button"
          onClick={() => navigate('/accounts')}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-[#0074CD] bg-white border-2 border-[#0074CD] rounded-lg"
        >
          Back to accounts
        </button>
      </div>
    </div>
  );
}
