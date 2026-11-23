import { useEffect, useRef } from 'react';

interface WarningDialogProps {
  heading: string;
  body: string;
  payee: string;
  amount: number;
  reference: string;
  allowedActions: string[];
  policyAllowsContinue: boolean;
  onStop: () => void;
  onContinue: () => void;
  isSubmitting: boolean;
}

export function WarningDialog({
  heading,
  body,
  payee,
  amount,
  reference,
  allowedActions,
  policyAllowsContinue,
  onStop,
  onContinue,
  isSubmitting,
}: WarningDialogProps) {
  const headingRef = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    // Focus moves to heading on mount
    headingRef.current?.focus();
  }, []);

  const formatAmount = (amountMinor: number): string => {
    return `£${(amountMinor / 100).toFixed(2)}`;
  };

  const showContinue = allowedActions.includes('continue') && policyAllowsContinue;

  return (
    <div role="alertdialog" aria-labelledby="warning-heading" aria-describedby="warning-body">
      {/* Warning header with icon and text */}
      <div className="flex gap-3 p-4 border-[3px] border-[#BE222A] rounded-lg bg-white">
        <svg
          className="w-8 h-8 flex-shrink-0 text-[#BE222A]"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path d="M12 3l10 18H2z" />
          <path d="M12 10v5M12 18v.5" />
        </svg>
        <div>
          <h3
            id="warning-heading"
            ref={headingRef}
            tabIndex={-1}
            className="text-2xl leading-tight font-bold text-black m-0"
          >
            {heading}
          </h3>
          <p id="warning-body" className="mt-1 text-black">
            {body}
          </p>
        </div>
      </div>

      {/* Warning tips */}
      <ul className="list-disc pl-5 text-black">
        <li className="mb-1">Be careful if someone asked you to move money quickly.</li>
        <li className="mb-1">Your bank will never ask you to move money to a safe account.</li>
        <li className="mb-1">If you are not sure, stop and speak to someone you trust.</li>
      </ul>

      {/* Payment details */}
      <dl className="m-0 border border-[#767676] rounded-lg bg-white">
        <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
          <dt className="text-sm text-[#4F5155]">To</dt>
          <dd className="m-0 font-bold text-black text-right">{payee}</dd>
        </div>
        <div className="flex justify-between gap-3 p-4 border-b border-[#E0E0E0]">
          <dt className="text-sm text-[#4F5155]">Amount</dt>
          <dd className="m-0 font-bold text-black text-right">{formatAmount(amount)}</dd>
        </div>
        <div className="flex justify-between gap-3 p-4">
          <dt className="text-sm text-[#4F5155]">Payment reference</dt>
          <dd className="m-0 font-bold text-black text-right">{reference}</dd>
        </div>
      </dl>

      {/* Stop button (always shown, default action) */}
      <button
        type="button"
        onClick={onStop}
        disabled={isSubmitting}
        className="flex items-center justify-center min-h-12 w-full px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg disabled:opacity-50"
      >
        Stop this payment
      </button>

      {/* Continue button (only when policy allows) */}
      {showContinue && (
        <button
          type="button"
          onClick={onContinue}
          disabled={isSubmitting}
          className="flex items-center justify-center min-h-12 w-full px-6 font-bold text-[#BE222A] bg-white border-2 border-[#BE222A] rounded-lg disabled:opacity-50"
        >
          I understand the risk, continue
        </button>
      )}

      {/* Guidance text */}
      <p className="text-sm text-[#4F5155] m-0">
        {showContinue
          ? 'Stop is the first and default action. If you continue, we record that you saw this warning before the payment goes on.'
          : 'The Continue control is not shown because the governed rules do not allow it.'}
      </p>

      {/* Live region for screen readers */}
      <div className="sr-only" role="status" aria-live="assertive" aria-atomic="true">
        {heading}. {body}
      </div>
    </div>
  );
}
