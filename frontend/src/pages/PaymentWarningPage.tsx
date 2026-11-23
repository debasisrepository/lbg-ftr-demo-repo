import { useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { WarningDialog } from '../components/payments/WarningDialog';

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
  warning?: {
    heading: string;
    body: string;
    allowed_actions: string[];
    policy_allows_continue: boolean;
  };
  created_at: string;
  updated_at: string;
}

export function PaymentWarningPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const payment = location.state?.payment as PaymentReviewResponse | undefined;
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!payment || payment.current_state !== 'warning_presented') {
      navigate('/accounts');
    }
  }, [payment, navigate]);

  if (!payment || !payment.warning) {
    return null;
  }

  const handleStop = async () => {
    setIsSubmitting(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL ?? '/api'}/v1/payments/${payment.payment_id}/warning-decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          review_version: payment.review_version,
          decision: 'stop',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to stop payment');
      }

      const stoppedPayment: PaymentReviewResponse = await response.json();
      
      // Navigate to outcome page showing "Payment not sent"
      navigate('/payment-outcome', {
        state: {
          payment: stoppedPayment,
          wasStopped: true,
        }
      });

    } catch (err) {
      console.error('Failed to stop payment:', err);
      setIsSubmitting(false);
    }
  };

  const handleContinue = async () => {
    if (!payment.warning?.policy_allows_continue) {
      return;
    }

    setIsSubmitting(true);
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL ?? '/api'}/v1/payments/${payment.payment_id}/warning-decision`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`,
        },
        body: JSON.stringify({
          review_version: payment.review_version,
          decision: 'continue',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        
        // Handle 403 when continue not permitted
        if (response.status === 403) {
          alert('You cannot continue with this payment. Please stop it.');
          setIsSubmitting(false);
          return;
        }
        
        throw new Error(errorData.detail || 'Failed to continue payment');
      }

      const continuedPayment: PaymentReviewResponse = await response.json();
      
      // Navigate to outcome page showing pending/sent status
      navigate('/payment-outcome', {
        state: { payment: continuedPayment }
      });

    } catch (err) {
      console.error('Failed to continue payment:', err);
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
        <span>9:41</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        <WarningDialog
          heading={payment.warning.heading}
          body={payment.warning.body}
          payee={payment.payee.payee_name}
          amount={payment.amount_minor}
          reference={payment.payment_reference}
          allowedActions={payment.warning.allowed_actions}
          policyAllowsContinue={payment.warning.policy_allows_continue}
          onStop={handleStop}
          onContinue={handleContinue}
          isSubmitting={isSubmitting}
        />
      </div>
    </div>
  );
}
