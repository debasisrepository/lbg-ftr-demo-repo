/**
 * PaymentSentPage - shown for completed payment state (wireframe_07 A/B).
 * Calls GET /api/v1/payments/{payment_id} to fetch outcome details.
 * Shows Sent badge (green, icon+text, never color alone), payment details,
 * payment reference (always shown), expected_arrival_time (only when supplied by hub).
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

export function PaymentSentPage() {
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
      
      // Verify status is Sent
      if (data.customer_visible_status !== 'Sent') {
        // Navigate to appropriate page based on status
        if (data.customer_visible_status === 'Failed') {
          navigate(`/payment-failed/${id}`, { state: { payment: data }, replace: true });
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

  const formatExpectedArrival = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const isToday = date.toDateString() === now.toDateString();
    
    const timeStr = date.toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    });
    
    if (isToday) {
      return `Today by ${timeStr}`;
    }
    
    const dateStr = date.toLocaleDateString('en-GB', {
      day: 'numeric',
      month: 'short',
    });
    return `${dateStr} by ${timeStr}`;
  };

  const hasExpectedArrival = payment.expected_arrival_time !== null;

  return (
    <div className="min-h-screen flex flex-col bg-[#0074CD]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold text-white">
        <span>9:41</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        {/* Success icon */}
        <svg
          className="w-12 h-12 text-white"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle cx="12" cy="12" r="10" />
          <path d="M7 12.5l3.5 3.5L17 9" />
        </svg>

        <h1 className="text-[28px] leading-tight font-bold text-white m-0" tabIndex={-1}>
          Payment sent
        </h1>

        {/* Sent badge */}
        <OutcomeBadge status="Sent" />

        {/* Success message */}
        <p className="text-lg text-white m-0">
          Your payment of {formatAmount(payment.amount_minor)} to{' '}
          {payment.payee_display_name || payment.payee.payee_name} has been sent.
          {hasExpectedArrival && ` It should arrive within 2 hours.`}
        </p>

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
          <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm text-[#4F5155]">Status</dt>
            <dd className="m-0 font-bold text-black text-right">Sent</dd>
          </div>
          {hasExpectedArrival && (
            <div className="flex justify-between gap-3 p-4">
              <dt className="text-sm text-[#4F5155]">Expected to arrive</dt>
              <dd className="m-0 font-bold text-black text-right">
                {formatExpectedArrival(payment.expected_arrival_time!)}
              </dd>
            </div>
          )}
          {!hasExpectedArrival && (
            <div className="flex justify-between gap-3 p-4">
              <dt className="text-sm text-[#4F5155]">From</dt>
              <dd className="m-0 font-bold text-black text-right">
                {payment.source_account.display_name}
              </dd>
            </div>
          )}
        </dl>

        {/* Action buttons */}
        <button
          type="button"
          onClick={() => navigate('/accounts')}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-[#0074CD] bg-white border-2 border-white rounded-lg"
        >
          Back to accounts
        </button>

        <button
          type="button"
          onClick={() => navigate('/payees')}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-white rounded-lg"
        >
          Make another payment
        </button>
      </div>
    </div>
  );
}
