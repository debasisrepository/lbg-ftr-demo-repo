import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Button,
  TextInput,
  InlineNotification,
  Modal,
  Theme,
} from '@carbon/react';
import { ArrowLeft, Checkmark, ChevronRight } from '@carbon/icons-react';
import apiClient from '../lib/api-client';
import type {
  Account,
  Payee,
  PaymentPrepareRequest,
  PaymentPrepareResponse,
  PaymentApproveRequest,
  PaymentApproveResponse,
} from '../types';
import styles from './PaymentEntryPage.module.scss';

export default function PaymentEntryPage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get payee and account from navigation state
  const selectedPayee = location.state?.payee as Payee | undefined;
  const selectedAccount = location.state?.account as Account | undefined;
  
  const [amount, setAmount] = useState('250.00');
  const [reference, setReference] = useState('');
  const [amountError, setAmountError] = useState<string | null>(null);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [warningMessage, setWarningMessage] = useState<string | null>(null);
  const [showWarningModal, setShowWarningModal] = useState(false);
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [prepareResponse, setPrepareResponse] = useState<PaymentPrepareResponse | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedPayee || !selectedAccount) {
      navigate('/payees');
    }
  }, [selectedPayee, selectedAccount, navigate]);

  if (!selectedPayee || !selectedAccount) {
    return null;
  }

  const formatCurrency = (minor: number): string => {
    const value = (minor / 100).toFixed(2);
    const [whole, decimal] = value.split('.');
    const withCommas = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return `${withCommas}.${decimal}`;
  };

  const parseCurrencyToMinor = (value: string): number => {
    const cleaned = value.replace(/[^0-9.]/g, '');
    const parsed = parseFloat(cleaned);
    return isNaN(parsed) ? 0 : Math.round(parsed * 100);
  };

  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setAmount(e.target.value);
    setAmountError(null);
  };

  const handleReferenceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length <= 18) {
      setReference(value);
    }
  };

  const validateAndPrepare = async () => {
    setAmountError(null);
    setGeneralError(null);
    setWarningMessage(null);

    const amountMinor = parseCurrencyToMinor(amount);
    
    if (amountMinor <= 0) {
      setAmountError('Please enter a valid amount');
      return;
    }

    setLoading(true);

    try {
      const request: PaymentPrepareRequest = {
        profile_id: 2, // Using personal profile from seed data
        source_account_id: selectedAccount.account_id,
        payee_id: selectedPayee.payee_id,
        amount_minor: amountMinor,
        currency: 'GBP',
        reference: reference || undefined,
      };

      const response = await apiClient.post<PaymentPrepareResponse>(
        '/payments/prepare',
        request
      );

      setPrepareResponse(response);

      // Check balance validation
      if (!response.balance_check.passed) {
        setAmountError(
          response.balance_check.detail ||
          `Payment amount exceeds available balance. You can pay up to £${formatCurrency(response.balance_check.available_balance_minor)} from this account.`
        );
        setLoading(false);
        return;
      }

      // Check limit validation
      if (!response.limit_check.passed) {
        setAmountError(
          response.limit_check.detail ||
          'Payment amount exceeds the permitted payment limit.'
        );
        setLoading(false);
        return;
      }

      // Check fraud decision
      if (response.fraud_decision.decision === 'hold') {
        setGeneralError(
          response.fraud_decision.hold_reason ||
          "We've paused this payment. We need to check it before it can be sent. Nothing has left your account."
        );
        setLoading(false);
        return;
      }

      if (response.fraud_decision.decision === 'warn') {
        setWarningMessage(
          response.fraud_decision.warning_message ||
          "Check this payment carefully. Fraudsters can pretend to be landlords or suppliers. Only continue if you're sure who you're paying."
        );
        setShowWarningModal(true);
        setLoading(false);
        return;
      }

      // Show approval modal
      setShowApprovalModal(true);
      setLoading(false);
    } catch (err) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to prepare payment');
      setLoading(false);
    }
  };

  const handleCancelWarning = () => {
    setShowWarningModal(false);
    setWarningMessage(null);
    setPrepareResponse(null);
  };

  const handleContinueAfterWarning = () => {
    setShowWarningModal(false);
    setShowApprovalModal(true);
  };

  const handleCancelApproval = () => {
    setShowApprovalModal(false);
    setPrepareResponse(null);
  };

  const handleApprove = async () => {
    if (!prepareResponse?.approval_challenge) {
      return;
    }

    setLoading(true);

    try {
      const approveRequest: PaymentApproveRequest = {
        challenge_id: prepareResponse.approval_challenge.challenge_id,
        method: 'dynamic_link',
        device_id: 'test-device',
      };

      const response = await apiClient.post<PaymentApproveResponse>(
        `/payments/${prepareResponse.payment_id}/approve`,
        approveRequest
      );

      // Navigate to outcome page with payment result
      navigate('/payment/outcome', { state: { payment: response } });
    } catch (err) {
      setGeneralError(err instanceof Error ? err.message : 'Failed to approve payment');
      setShowApprovalModal(false);
      setLoading(false);
    }
  };

  const availableBalance = selectedAccount.available_balance_minor ?? selectedAccount.current_balance_minor;

  return (
    <Theme theme="white">
      <div className={styles.container}>
        <header className={styles.topbar}>
          <button
            className={styles.backButton}
            type="button"
            aria-label="Back to payees"
            onClick={() => navigate('/payees')}
          >
            <ArrowLeft size={16} />
          </button>
          <span className={styles.brand}>Your Bank</span>
        </header>

        <main className={styles.content}>
          <h1 className={styles.title}>Make a payment</h1>

          <div className={styles.payeePanel} aria-label={`Paying ${selectedPayee.display_name}`}>
            <div>
              <p className={styles.payeeName}>{selectedPayee.display_name}</p>
              <p className={styles.payeeAccount}>
                {selectedPayee.sort_code} · {selectedPayee.masked_account_number}
              </p>
            </div>
            <Checkmark size={20} className={styles.checkIcon} />
          </div>

          <form className={styles.form} onSubmit={(e) => { e.preventDefault(); validateAndPrepare(); }}>
            <div className={styles.field}>
              <label htmlFor="from" className={styles.label}>From</label>
              <input
                id="from"
                type="text"
                className={styles.inputReadonly}
                readOnly
                value={`${selectedAccount.account_name} · ${selectedAccount.sort_code} | ${selectedAccount.masked_account_number}`}
                aria-describedby="from-helper"
              />
              <p id="from-helper" className={styles.helper}>
                Available balance £{formatCurrency(availableBalance)}
              </p>
            </div>

            <div className={styles.field}>
              <label htmlFor="amount" className={styles.label}>Amount</label>
              <div className={styles.amountWrapper}>
                <span className={styles.currencyPrefix} aria-hidden="true">£</span>
                <input
                  id="amount"
                  type="text"
                  inputMode="decimal"
                  className={`${styles.input} ${styles.amountInput} ${amountError ? styles.inputInvalid : ''}`}
                  value={amount}
                  onChange={handleAmountChange}
                  aria-describedby="amount-helper"
                  aria-invalid={!!amountError}
                />
              </div>
              <p id="amount-helper" className={styles.helper}>
                Payments are in pounds sterling (GBP).
              </p>
              {amountError && (
                <p className={styles.errorMessage} role="alert">
                  <svg className={styles.errorIcon} width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                    <path d="M8,1C4.1,1,1,4.1,1,8s3.1,7,7,7s7-3.1,7-7S11.9,1,8,1z M10.7,11.5L4.5,5.3l0.8-0.8l6.2,6.2L10.7,11.5z"/>
                  </svg>
                  {amountError}
                </p>
              )}
            </div>

            <div className={styles.field}>
              <label htmlFor="reference" className={styles.label}>Reference (optional)</label>
              <input
                id="reference"
                type="text"
                maxLength={18}
                className={styles.input}
                value={reference}
                onChange={handleReferenceChange}
                aria-describedby="reference-helper"
              />
              <p id="reference-helper" className={styles.helper}>
                Up to 18 characters.
              </p>
            </div>

            <InlineNotification
              kind="info"
              title="You'll approve with Face ID"
              subtitle={`Your approval is tied to ${selectedPayee.display_name} and £${amount}. If you change either, you'll need to approve again.`}
              lowContrast
              hideCloseButton
            />

            {generalError && (
              <InlineNotification
                kind="error"
                title={generalError.includes('paused') ? "We've paused this payment" : 'Error'}
                subtitle={generalError}
                lowContrast
                hideCloseButton
              />
            )}

            <Button
              type="submit"
              className={styles.payButton}
              disabled={loading || !amount}
              renderIcon={ChevronRight}
            >
              Pay £{amount || '0.00'}
            </Button>
          </form>
        </main>

        {/* Fraud warning modal */}
        <Modal
          open={showWarningModal}
          modalHeading="Check this payment carefully"
          primaryButtonText="I'm sure, continue"
          secondaryButtonText="Cancel payment"
          onRequestSubmit={handleContinueAfterWarning}
          onSecondarySubmit={handleCancelWarning}
          onRequestClose={handleCancelWarning}
        >
          <p>{warningMessage}</p>
        </Modal>

        {/* Approval modal */}
        <Modal
          open={showApprovalModal}
          modalHeading="Approve with Face ID"
          primaryButtonText="Approve"
          secondaryButtonText="Cancel"
          onRequestSubmit={handleApprove}
          onSecondarySubmit={handleCancelApproval}
          onRequestClose={handleCancelApproval}
        >
          {prepareResponse && (
            <div className={styles.approvalContent}>
              <svg className={styles.faceIdIcon} width="48" height="48" viewBox="0 0 32 32" fill="currentColor">
                <path d="M16,2A14,14,0,1,0,30,16,14,14,0,0,0,16,2Zm0,26A12,12,0,1,1,28,16,12,12,0,0,1,16,28Z"/>
                <path d="M11.5,11A2.5,2.5,0,1,0,14,13.5,2.48,2.48,0,0,0,11.5,11Z"/>
                <path d="M20.5,11A2.5,2.5,0,1,0,23,13.5,2.48,2.48,0,0,0,20.5,11Z"/>
                <path d="M9,20a8.13,8.13,0,0,0,14,0Z"/>
              </svg>
              
              <dl className={styles.approvalSummary}>
                <div className={styles.summaryRow}>
                  <dt>Pay</dt>
                  <dd>{prepareResponse.payee.display_name}</dd>
                </div>
                <div className={styles.summaryRow}>
                  <dt>Amount</dt>
                  <dd>£{formatCurrency(prepareResponse.amount_minor)}</dd>
                </div>
              </dl>

              <p className={styles.approvalNote}>
                Face ID is checked on your phone. Changing the payee or amount cancels this approval.
              </p>
            </div>
          )}
        </Modal>
      </div>
    </Theme>
  );
}
