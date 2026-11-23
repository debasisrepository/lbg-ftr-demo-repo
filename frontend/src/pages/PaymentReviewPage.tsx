import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { ApprovalSheet } from '../components/payments/ApprovalSheet';

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

export function PaymentReviewPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const payment = location.state?.payment as PaymentReviewResponse | undefined;
  const idempotencyKey = location.state?.idempotencyKey as string | undefined;
  
  const [showApprovalSheet, setShowApprovalSheet] = useState(false);
  const [showChangeNotice, setShowChangeNotice] = useState(false);
  const [currentPayment, setCurrentPayment] = useState(payment);

  useEffect(() => {
    if (!payment) {
      navigate('/payees');
    }
  }, [payment, navigate]);

  useEffect(() => {
    // Check if we came back from payment entry with updated details
    if (location.state?.changed) {
      setShowChangeNotice(true);
      setCurrentPayment(location.state.payment);
    }
  }, [location.state]);

  const handleApproveClick = () => {
    setShowApprovalSheet(true);
  };

  const handleChangeDetails = () => {
    if (!currentPayment) return;
    // Navigate back to payment entry with current payment details
    navigate('/payment-entry', {
      state: {
        payee: {
          payee_id: currentPayment.payee.payee_id,
          payee_name: currentPayment.payee.payee_name,
          payee_sort_code: '', // Not available in payment response
          masked_account_identifier: currentPayment.payee.masked_account_identifier,
        },
        editingPayment: currentPayment,
      }
    });
  };

  const handleApprovalSuccess = (payment: PaymentReviewResponse) => {
    // After successful approval, navigate based on status
    // The backend processes approval and sets customer_visible_status
    // If not set yet, navigate to payment-outcome which will handle polling
    
    const paymentId = payment.payment_id;
    
    // Navigate to payment-outcome with the payment data
    // PaymentOutcomePage will redirect to sent/failed/pending based on final status
    navigate('/payment-outcome', { state: { payment }, replace: true });
  };

  const handleApprovalFailure = () => {
    // Navigate to failure outcome page
    navigate('/payment-outcome', { 
      state: { 
        payment: currentPayment,
        wasStopped: true
      } 
    });
  };

  if (!currentPayment) {
    return null;
  }

  const formatAmount = (amountMinor: number): string => {
    return `£${(amountMinor / 100).toFixed(2)}`;
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8] relative">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
        <span>9:41</span>
      </div>

      {/* Top bar */}
      <div className="flex items-center px-2 bg-white">
        <button
          type="button"
          onClick={() => navigate('/payment-entry', {
            state: {
              payee: {
                payee_id: currentPayment.payee.payee_id,
                payee_name: currentPayment.payee.payee_name,
                masked_account_identifier: currentPayment.payee.masked_account_identifier,
              }
            }
          })}
          className="inline-flex items-center justify-center min-w-11 min-h-11 text-[#0074CD] font-bold bg-transparent border-0 cursor-pointer"
          aria-label="Back to payment entry"
        >
          Back
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        <h1 className="text-[28px] leading-tight font-bold text-[#002563] m-0" tabIndex={-1}>
          Review your payment
        </h1>

        {/* Change notice */}
        {showChangeNotice && (
          <div className="flex gap-3 p-4 rounded-lg border-l-4 border-[#0074CD] bg-[#F2FAFF]" role="status">
            <svg className="w-5 h-5 flex-shrink-0 text-[#0074CD]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 11v6M12 7.5v.5" />
            </svg>
            <div className="text-[#002563]">
              <strong className="block font-bold">The payment details changed</strong>
              <span>Review them again before you approve. Your earlier approval no longer applies.</span>
            </div>
          </div>
        )}

        <p className="text-sm text-[#4F5155] m-0">
          Check these details. Your approval applies only to this payment. Nothing has been sent yet.
        </p>

        {/* Review details */}
        <dl className="m-0 border-2 border-[#002563] rounded-lg bg-white">
          <div className="p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm font-bold text-[#4F5155]">From</dt>
            <dd className="mt-0.5 text-lg font-bold text-black">
              {currentPayment.source_account.display_name}
              <small className="block text-sm font-normal text-[#4F5155]">
                Account ending {currentPayment.source_account.masked_account_identifier}
              </small>
            </dd>
          </div>
          <div className="p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm font-bold text-[#4F5155]">To</dt>
            <dd className="mt-0.5 text-lg font-bold text-black">
              {currentPayment.payee.payee_name}
              <small className="block text-sm font-normal text-[#4F5155]">
                Account ending {currentPayment.payee.masked_account_identifier}
              </small>
            </dd>
          </div>
          <div className="p-4 border-b border-[#E0E0E0]">
            <dt className="text-sm font-bold text-[#4F5155]">Amount</dt>
            <dd className="mt-0.5 text-[32px] leading-tight font-bold text-[#002563]">
              {formatAmount(currentPayment.amount_minor)}
            </dd>
          </div>
          <div className="p-4">
            <dt className="text-sm font-bold text-[#4F5155]">Payment reference</dt>
            <dd className="mt-0.5 text-lg font-bold text-black">
              {currentPayment.payment_reference}
            </dd>
          </div>
        </dl>

        <p className="text-sm text-[#4F5155] m-0">
          Payment not sent yet. Review and approve it to send.
        </p>

        {/* Action buttons */}
        <button
          type="button"
          onClick={handleApproveClick}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg"
        >
          Approve payment
        </button>

        <button
          type="button"
          onClick={handleChangeDetails}
          className="flex items-center justify-center min-h-12 px-6 font-bold text-[#0074CD] bg-white border-2 border-[#0074CD] rounded-lg"
        >
          Change details
        </button>
      </div>

      {/* Approval sheet overlay */}
      {showApprovalSheet && (
        <ApprovalSheet
          payment={currentPayment}
          idempotencyKey={idempotencyKey || crypto.randomUUID()}
          onClose={() => setShowApprovalSheet(false)}
          onSuccess={handleApprovalSuccess}
          onFailure={handleApprovalFailure}
        />
      )}
    </div>
  );
}
