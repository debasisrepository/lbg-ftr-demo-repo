import { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { apiClient, ApiError } from '../lib/api-client';

interface PayeeItem {
  payee_id: string;
  payee_name: string;
  payee_sort_code: string;
  masked_account_identifier: string;
}

interface AccountItem {
  account_id: string;
  account_type: string;
  display_name: string;
  masked_account_identifier: string;
  balance: {
    availability_state: 'current' | 'stale' | 'unavailable' | 'unknown';
    amount_minor: number | null;
    currency: string | null;
    display_text: string;
  };
  as_of_timestamp: string;
  freshness_status: 'within_target' | 'breached' | 'unknown';
  freshness_text: string;
  item_state: 'available' | 'partial';
  payment_source_eligible: boolean;
}

interface AccountsResponse {
  items: AccountItem[];
  total: number;
  page: number;
  page_size: number;
}

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

interface ValidationError {
  field: string;
  message: string;
}

export function PaymentEntryPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const payee = location.state?.payee as PayeeItem | undefined;
  
  const [accounts, setAccounts] = useState<AccountItem[]>([]);
  const [sourceAccountId, setSourceAccountId] = useState('');
  const [amount, setAmount] = useState('');
  const [reference, setReference] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationError[]>([]);
  const [showErrors, setShowErrors] = useState(false);
  const idempotencyKeyRef = useRef<string>(crypto.randomUUID());

  useEffect(() => {
    if (!payee) {
      navigate('/payees');
      return;
    }
    fetchAccounts();
  }, [payee, navigate]);

  const fetchAccounts = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.get<AccountsResponse>('/v1/accounts/');
      // Filter to payment_source_eligible accounts only
      const eligibleAccounts = response.items.filter(acc => acc.payment_source_eligible);
      setAccounts(eligibleAccounts);
      if (eligibleAccounts.length > 0) {
        setSourceAccountId(eligibleAccounts[0].account_id);
      }
    } catch (err) {
      console.error('Failed to fetch accounts:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const validateForm = (): boolean => {
    const errors: ValidationError[] = [];

    if (!sourceAccountId) {
      errors.push({ field: 'source_account_id', message: 'Choose an account to pay from.' });
    }

    const amountNum = parseFloat(amount);
    if (!amount || isNaN(amountNum) || amountNum <= 0) {
      errors.push({ field: 'amount', message: 'Enter an amount greater than £0.00.' });
    }

    if (!reference || reference.trim().length === 0) {
      errors.push({ field: 'payment_reference', message: 'Enter a payment reference.' });
    } else if (reference.length > 18) {
      errors.push({ field: 'payment_reference', message: 'Payment reference must be 18 characters or less.' });
    }

    setValidationErrors(errors);
    return errors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setShowErrors(true);

    if (!validateForm()) {
      return;
    }

    if (!payee) {
      return;
    }

    setIsSubmitting(true);

    try {
      const amountMinor = Math.round(parseFloat(amount) * 100);

      const response = await fetch(`${import.meta.env.VITE_API_URL ?? '/api'}/v1/payments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${sessionStorage.getItem('auth_token')}`,
          'Idempotency-Key': idempotencyKeyRef.current,
        },
        body: JSON.stringify({
          source_account_id: sourceAccountId,
          payee_id: payee.payee_id,
          amount_minor: amountMinor,
          currency: 'GBP',
          payment_reference: reference.trim(),
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new ApiError(`Request failed: ${response.status}`, response.status, errorData.detail);
      }

      const paymentReview: PaymentReviewResponse = await response.json();
      
      // Navigate to review page with payment details
      navigate('/payment-review', { 
        state: { 
          payment: paymentReview,
          idempotencyKey: idempotencyKeyRef.current
        } 
      });

    } catch (err) {
      console.error('Failed to create payment:', err);
      if (err instanceof ApiError) {
        setValidationErrors([{ field: 'submit', message: err.detail || err.message }]);
      } else {
        setValidationErrors([{ field: 'submit', message: 'Failed to create payment. Please try again.' }]);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // Allow only valid decimal input
    if (/^\d*\.?\d{0,2}$/.test(value) || value === '') {
      setAmount(value);
    }
  };

  const handleReferenceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= 18) {
      setReference(value);
    }
  };

  const getFieldError = (field: string): string | undefined => {
    if (!showErrors) return undefined;
    return validationErrors.find(e => e.field === field)?.message;
  };

  const isFormValid = !isLoading && sourceAccountId && amount && parseFloat(amount) > 0 && reference.trim().length > 0;

  if (!payee) {
    return null;
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
        <span>9:41</span>
      </div>

      {/* Top bar */}
      <div className="flex items-center px-2 bg-white">
        <button
          type="button"
          onClick={() => navigate('/payees')}
          className="inline-flex items-center justify-center min-w-11 min-h-11 text-[#0074CD] font-bold bg-transparent border-0 cursor-pointer"
          aria-label="Back to saved payees"
        >
          Back
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        <h1 className="text-[28px] leading-tight font-bold text-[#002563] m-0">Pay {payee.payee_name}</h1>
        <p className="text-sm text-[#4F5155] mt-0 mb-0">
          Sort code {payee.payee_sort_code}, account ending {payee.masked_account_identifier}
        </p>

        {/* Validation summary */}
        {showErrors && validationErrors.length > 0 && (
          <div className="flex flex-col gap-1 p-4 rounded-lg border-2 border-[#BE222A] bg-white" role="alert">
            <strong className="font-bold text-black">Fix {validationErrors.length} {validationErrors.length === 1 ? 'thing' : 'things'} to continue</strong>
            <ul className="list-disc ml-5 mt-1 mb-0">
              {validationErrors.map((error, index) => (
                <li key={index}>
                  <a href={`#${error.field}`} className="text-black underline">
                    {error.message}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0074CD]" role="status"></div>
          </div>
        ) : (
          <form onSubmit={handleSubmit} noValidate className="flex flex-col gap-4">
            {/* Source account picker */}
            <div>
              <label htmlFor="source_account_id" className="block mb-1 text-sm font-bold text-black">
                From
              </label>
              <select
                id="source_account_id"
                name="source_account_id"
                value={sourceAccountId}
                onChange={(e) => setSourceAccountId(e.target.value)}
                className="block w-full h-14 px-4 text-base text-black bg-white border border-[#767676] rounded-lg"
                aria-describedby="source_account_id-hint"
              >
                {accounts.map((account) => {
                  const displayBalance = account.balance.availability_state === 'unavailable' || account.balance.availability_state === 'unknown'
                    ? 'Balance unavailable'
                    : account.balance.display_text;
                  return (
                    <option key={account.account_id} value={account.account_id}>
                      {account.display_name}, ending {account.masked_account_identifier} - {displayBalance}
                    </option>
                  );
                })}
              </select>
              <p id="source_account_id-hint" className="mt-1 text-sm text-[#4F5155]">
                Only accounts that can be paid from are listed. An unavailable balance shows as unavailable, never as £0.00.
              </p>
            </div>

            {/* Amount input */}
            <div>
              <label htmlFor="amount" className="block mb-1 text-sm font-bold text-black">
                Amount (£)
              </label>
              <input
                type="text"
                id="amount"
                name="amount"
                inputMode="decimal"
                value={amount}
                onChange={handleAmountChange}
                className={`block w-full h-14 px-4 text-base text-black bg-white rounded-lg ${
                  getFieldError('amount') ? 'border-2 border-[#BE222A]' : 'border border-[#767676]'
                }`}
                aria-invalid={!!getFieldError('amount')}
                aria-describedby={getFieldError('amount') ? 'amount-error' : 'amount-hint'}
              />
              {getFieldError('amount') ? (
                <p id="amount-error" className="mt-1 flex gap-2 text-sm font-bold text-[#BE222A]">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 3l10 18H2z" />
                    <path d="M12 10v5M12 18v.5" />
                  </svg>
                  <span>{getFieldError('amount')}</span>
                </p>
              ) : (
                <p id="amount-hint" className="mt-1 text-sm text-[#4F5155]">
                  Enter pounds and pence, for example 250.00.
                </p>
              )}
            </div>

            {/* Reference input */}
            <div>
              <label htmlFor="payment_reference" className="block mb-1 text-sm font-bold text-black">
                Payment reference <span className="float-right font-normal text-[#4F5155]" aria-hidden="true">{reference.length} of 18</span>
              </label>
              <input
                type="text"
                id="payment_reference"
                name="payment_reference"
                maxLength={18}
                value={reference}
                onChange={handleReferenceChange}
                className={`block w-full h-14 px-4 text-base text-black bg-white rounded-lg ${
                  getFieldError('payment_reference') ? 'border-2 border-[#BE222A]' : 'border border-[#767676]'
                }`}
                aria-invalid={!!getFieldError('payment_reference')}
                aria-describedby={getFieldError('payment_reference') ? 'payment_reference-error' : 'payment_reference-hint'}
              />
              {getFieldError('payment_reference') ? (
                <p id="payment_reference-error" className="mt-1 flex gap-2 text-sm font-bold text-[#BE222A]">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
                    <path d="M12 3l10 18H2z" />
                    <path d="M12 10v5M12 18v.5" />
                  </svg>
                  <span>{getFieldError('payment_reference')}</span>
                </p>
              ) : (
                <p id="payment_reference-hint" className="mt-1 text-sm text-[#4F5155]">
                  1 to 18 characters. The payee sees this on their statement. You will check it again before you approve.
                </p>
              )}
            </div>

            {/* Submit button */}
            <button
              type="submit"
              disabled={!isFormValid || isSubmitting}
              aria-disabled={!isFormValid || isSubmitting}
              className={`flex items-center justify-center min-h-12 px-6 font-bold rounded-lg ${
                isFormValid && !isSubmitting
                  ? 'text-white bg-[#0074CD] border-2 border-[#0074CD]'
                  : 'text-[#4F5155] bg-[#E0E0E0] border-2 border-[#E0E0E0]'
              }`}
            >
              {isSubmitting ? 'Creating...' : 'Review payment'}
            </button>

            {!isFormValid && (
              <p className="text-sm text-[#4F5155] mt-0 mb-0">
                The button stays off until the source account, amount and reference are complete. Nothing is sent from this screen.
              </p>
            )}
          </form>
        )}
      </div>
    </div>
  );
}
