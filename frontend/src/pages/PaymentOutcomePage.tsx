import { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button, InlineNotification, Theme } from '@carbon/react';
import { ChevronRight, Checkmark, Time, Close } from '@carbon/icons-react';
import apiClient from '../lib/api-client';
import type { PaymentApproveResponse, PaymentStatusResponse } from '../types';
import styles from './PaymentOutcomePage.module.scss';

export default function PaymentOutcomePage() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get payment from navigation state
  const initialPayment = location.state?.payment as PaymentApproveResponse | undefined;
  
  const [payment, setPayment] = useState<PaymentApproveResponse | PaymentStatusResponse | null>(
    initialPayment || null
  );
  const [loading, setLoading] = useState(!initialPayment);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // If we don't have payment data, redirect to accounts
    if (!payment && !loading) {
      navigate('/accounts');
    }

    // If we have a payment ID in URL params, fetch current status
    const params = new URLSearchParams(location.search);
    const paymentId = params.get('id');
    
    if (paymentId) {
      fetchPaymentStatus(parseInt(paymentId));
    }
  }, []);

  const fetchPaymentStatus = async (paymentId: number) => {
    try {
      setLoading(true);
      const response = await apiClient.get<PaymentStatusResponse>(
        `/payments/${paymentId}`
      );
      setPayment(response);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load payment status');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Theme theme="white">
        <div className={styles.container}>
          <p>Loading payment status...</p>
        </div>
      </Theme>
    );
  }

  if (error || !payment) {
    return (
      <Theme theme="white">
        <div className={styles.container}>
          <InlineNotification
            kind="error"
            title="Error"
            subtitle={error || 'Payment information not available'}
            lowContrast
          />
          <Button onClick={() => navigate('/accounts')}>Back to accounts</Button>
        </div>
      </Theme>
    );
  }

  const formatCurrency = (minor: number): string => {
    const value = (minor / 100).toFixed(2);
    const [whole, decimal] = value.split('.');
    const withCommas = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    return `${withCommas}.${decimal}`;
  };

  const getStatusIcon = () => {
    switch (payment.status) {
      case 'sent':
        return <Checkmark size={64} className={styles.iconSent} />;
      case 'pending':
        return <Time size={64} className={styles.iconPending} />;
      case 'failed':
        return <Close size={64} className={styles.iconFailed} />;
      default:
        return <Checkmark size={64} className={styles.iconSent} />;
    }
  };

  const getStatusBadge = () => {
    const statusClass = payment.status === 'sent' 
      ? styles.statusSent 
      : payment.status === 'pending' 
      ? styles.statusPending 
      : styles.statusFailed;

    const StatusIcon = payment.status === 'sent' 
      ? Checkmark 
      : payment.status === 'pending' 
      ? Time 
      : Close;

    return (
      <span className={`${styles.statusBadge} ${statusClass}`}>
        <StatusIcon size={16} />
        {payment.status.charAt(0).toUpperCase() + payment.status.slice(1)}
      </span>
    );
  };

  const getHeading = () => {
    switch (payment.status) {
      case 'sent':
        return 'Payment sent';
      case 'pending':
        return 'Payment pending';
      case 'failed':
        return 'Payment not sent';
      default:
        return 'Payment status';
    }
  };

  const getLeadText = () => {
    if (payment.status === 'sent') {
      return `£${formatCurrency(payment.amount_minor)} is on its way to ${payment.payee.display_name}. ${payment.expected_arrival_message || 'It should arrive within 2 hours.'}`;
    } else if (payment.status === 'pending') {
      return `We're waiting for confirmation that £${formatCurrency(payment.amount_minor)} has reached ${payment.payee.display_name}. We'll update this page as soon as we know.`;
    } else {
      return `We couldn't send £${formatCurrency(payment.amount_minor)} to ${payment.payee.display_name}. No money has left your account.`;
    }
  };

  const showDuplicateWarning = payment.duplicate_submission_blocked && payment.status === 'pending';
  const showFailureGuidance = payment.status === 'failed';

  return (
    <Theme theme="white">
      <div className={styles.container}>
        <header className={styles.topbar}>
          <span className={styles.brand}>Your Bank</span>
          <span className={styles.helper}>Personal profile</span>
        </header>

        <main className={styles.content}>
          <section className={`${styles.outcome} ${styles[`outcome${payment.status.charAt(0).toUpperCase()}${payment.status.slice(1)}`]}`}>
            {getStatusIcon()}
            {getStatusBadge()}
            <h1 className={styles.heading}>{getHeading()}</h1>
            <p className={styles.lead} role="status">{getLeadText()}</p>
          </section>

          <dl className={styles.summary} aria-label="Payment summary">
            <div className={styles.summaryRow}>
              <dt>Payee</dt>
              <dd>{payment.payee.display_name}</dd>
            </div>
            <div className={styles.summaryRow}>
              <dt>Amount</dt>
              <dd>£{formatCurrency(payment.amount_minor)}</dd>
            </div>
            {payment.reference && (
              <div className={styles.summaryRow}>
                <dt>Reference</dt>
                <dd>{payment.reference}</dd>
              </div>
            )}
            <div className={styles.summaryRow}>
              <dt>Payment identifier</dt>
              <dd>{payment.payment_reference}</dd>
            </div>
            {payment.status === 'sent' && payment.expected_arrival_message && (
              <div className={styles.summaryRow}>
                <dt>Expected arrival</dt>
                <dd>Within 2 hours</dd>
              </div>
            )}
            {payment.status === 'failed' && payment.failure_reason && (
              <div className={styles.summaryRow}>
                <dt>Reason</dt>
                <dd>{payment.failure_reason}</dd>
              </div>
            )}
          </dl>

          {showDuplicateWarning && (
            <InlineNotification
              kind="info"
              title="Don't pay again yet"
              subtitle="This payment is already being processed. Paying again could send the money twice."
              lowContrast
              hideCloseButton
            />
          )}

          {showFailureGuidance && (
            <InlineNotification
              kind="error"
              title="What to do next"
              subtitle="Check your balance, then try the payment again. If it keeps failing, contact us and quote the payment identifier."
              lowContrast
              hideCloseButton
            />
          )}

          <div className={styles.actions}>
            {payment.status === 'failed' ? (
              <>
                <Button
                  kind="primary"
                  renderIcon={ChevronRight}
                  onClick={() => navigate('/payees')}
                >
                  Try again
                </Button>
                <Button
                  kind="tertiary"
                  renderIcon={ChevronRight}
                  onClick={() => navigate('/accounts')}
                >
                  Back to accounts
                </Button>
              </>
            ) : (
              <>
                <Button
                  kind="primary"
                  renderIcon={ChevronRight}
                  onClick={() => navigate('/accounts')}
                >
                  Back to accounts
                </Button>
                <Button
                  kind="tertiary"
                  renderIcon={ChevronRight}
                  onClick={() => navigate('/payees')}
                  disabled={payment.status === 'pending'}
                >
                  Make another payment
                </Button>
              </>
            )}
          </div>
        </main>
      </div>
    </Theme>
  );
}
