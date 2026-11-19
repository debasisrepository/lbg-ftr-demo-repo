import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { InlineNotification, Theme } from '@carbon/react';
import { Checkmark, Time, WarningAlt } from '@carbon/icons-react';
import apiClient from '../lib/api-client';
import { useAuth } from '../lib/auth-context';
import { formatCurrency } from '../lib/utils';
import type { AccountsOverviewResponse, Account } from '../types';
import styles from './AccountsPage.module.scss';

export default function AccountsPage() {
  const navigate = useNavigate();
  const { activeProfileId } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AccountsOverviewResponse | null>(null);

  useEffect(() => {
    async function fetchAccounts() {
      try {
        setLoading(true);
        setError(null);
        
        if (!activeProfileId) {
          setError('No active profile available');
          setLoading(false);
          return;
        }
        
        const response = await apiClient.get<AccountsOverviewResponse>(`/accounts/overview?profile_id=${activeProfileId}`);
        setData(response);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load accounts');
      } finally {
        setLoading(false);
      }
    }

    fetchAccounts();
  }, [activeProfileId]);

  if (loading) {
    return (
      <Theme theme="white">
        <div className={styles.container}>
          <p>Loading accounts...</p>
        </div>
      </Theme>
    );
  }

  if (error) {
    return (
      <Theme theme="white">
        <div className={styles.container}>
          <InlineNotification
            kind="error"
            title="Error loading accounts"
            subtitle={error}
            lowContrast
          />
        </div>
      </Theme>
    );
  }

  if (!data) {
    return (
      <Theme theme="white">
        <div className={styles.container}>
          <p>No account data available</p>
        </div>
      </Theme>
    );
  }

  const { profile, accounts, data_gaps } = data;

  const getAccountBalance = (account: Account): string => {
    // For loans and credit cards, show absolute value of balance
    const balance = Math.abs(account.current_balance_minor);
    return formatCurrency(balance / 100);
  };

  const getFreshnessIcon = (state: string) => {
    if (state === 'current') {
      return <Checkmark size={16} />;
    } else if (state === 'delayed') {
      return <Time size={16} />;
    } else {
      return <WarningAlt size={16} />;
    }
  };

  const getFreshnessText = (account: Account): string => {
    if (account.freshness_state === 'current') {
      return 'Up to date';
    } else if (account.freshness_state === 'delayed') {
      const time = new Date(account.last_updated_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' });
      return `Delayed · last updated ${time} today. Figures may have changed.`;
    } else {
      return 'Unavailable. We can\'t show this balance right now. Try again later.';
    }
  };

  const getProfileBadgeIcon = () => {
    if (profile.profile_type === 'business') {
      return (
        <svg width="16" height="16" viewBox="0 0 32 32" fill="currentColor">
          <path d="M28,2H16a2.002,2.002,0,0,0-2,2V14H4a2.002,2.002,0,0,0-2,2V30H30V4A2.0023,2.0023,0,0,0,28,2ZM9,28V21h4v7Zm19,0H15V20a1,1,0,0,0-1-1H8a1,1,0,0,0-1,1v8H4V16H16V4H28Z"/>
          <rect x="18" y="8" width="2" height="2"/>
          <rect x="24" y="8" width="2" height="2"/>
          <rect x="18" y="14" width="2" height="2"/>
          <rect x="24" y="14" width="2" height="2"/>
          <rect x="18" y="19.9996" width="2" height="2"/>
          <rect x="24" y="19.9996" width="2" height="2"/>
        </svg>
      );
    } else {
      return (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
          <path d="M8,1C4.1,1,1,4.1,1,8s3.1,7,7,7s7-3.1,7-7S11.9,1,8,1z M5,13.2v-1.5c0-0.9,0.6-1.6,1.5-1.7h3c0.9,0.1,1.5,0.8,1.5,1.7v1.5C9.1,14.3,6.9,14.3,5,13.2L5,13.2z M12,12l0-0.8c0-0.9-1.1-2.1-2.5-2.2h-3C5.1,9.1,4,10.3,4,11.7l0,0.5v0.3c-2.5-2.2-2.7-6-0.5-8.5s6-2.7,8.5-0.5s2.7,6,0.5,8.5c-0.1,0.2-0.3,0.3-0.5,0.5V12z"/>
          <path d="M8,3C6.6,3,5.5,4.1,5.5,5.5S6.6,8,8,8s2.5-1.1,2.5-2.5S9.4,3,8,3z M8,7C7.2,7,6.5,6.3,6.5,5.5S7.2,4,8,4s1.5,0.7,1.5,1.5S8.8,7,8,7z"/>
        </svg>
      );
    }
  };

  return (
    <Theme theme="white">
      <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.profileBadge}>
          {getProfileBadgeIcon()}
          <span>Active profile: {profile.profile_type === 'business' ? 'Business' : 'Personal'}</span>
        </div>
        <h1 className={styles.title}>Accounts</h1>
      </div>

      <ul className={styles.accountsList}>
        {accounts.map((account) => (
          <li key={account.account_id}>
            <article className={`${styles.accountTile} ${account.freshness_state === 'delayed' || account.freshness_state === 'unavailable' ? styles.gapTile : ''}`}>
              <div className={styles.tileHead}>
                <div>
                  <h2 className={styles.accountName}>{account.account_name}</h2>
                  <p className={styles.accountSub}>
                    {account.sort_code && `${account.sort_code} | `}
                    {account.masked_account_number}
                    {account.freshness_state === 'delayed' && ' · illustrative figures'}
                  </p>
                </div>
              </div>
              
              <p className={styles.balance}>{getAccountBalance(account)}</p>
              
              {account.overdraft_available_minor !== null && account.overdraft_available_minor !== undefined && (
                <dl className={styles.keyValue}>
                  <dt>Available overdraft</dt>
                  <dd>{formatCurrency(account.overdraft_available_minor / 100)}</dd>
                </dl>
              )}
              
              {account.available_credit_minor !== null && account.available_credit_minor !== undefined && (
                <dl className={styles.keyValue}>
                  <dt>Available credit</dt>
                  <dd>{formatCurrency(account.available_credit_minor / 100)}</dd>
                </dl>
              )}
              
              {account.next_repayment_amount_minor !== null && account.next_repayment_amount_minor !== undefined && (
                <dl className={styles.keyValue}>
                  <dt>Next repayment</dt>
                  <dd>
                    {formatCurrency(account.next_repayment_amount_minor / 100)}
                    {account.next_repayment_due_date && ` · due ${new Date(account.next_repayment_due_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}`}
                  </dd>
                </dl>
              )}
              
              <p className={styles.freshness}>
                {getFreshnessIcon(account.freshness_state)}
                <span>{getFreshnessText(account)}</span>
              </p>
            </article>
          </li>
        ))}
      </ul>

      {data_gaps && data_gaps.length > 0 && (
        <InlineNotification
          kind="warning"
          title="Some loan details are delayed"
          subtitle="Your other accounts are up to date. We'll refresh the loan as soon as we can."
          lowContrast
        />
      )}

      <nav className={styles.tabBar}>
        <button className={`${styles.tab} ${styles.tabActive}`} onClick={() => navigate('/accounts')}>
          <svg width="24" height="24" viewBox="0 0 32 32" fill="currentColor">
            <path d="M28,2H16a2.002,2.002,0,0,0-2,2V14H4a2.002,2.002,0,0,0-2,2V30H30V4A2.0023,2.0023,0,0,0,28,2ZM9,28V21h4v7Zm19,0H15V20a1,1,0,0,0-1-1H8a1,1,0,0,0-1,1v8H4V16H16V4H28Z"/>
            <rect x="18" y="8" width="2" height="2"/>
            <rect x="24" y="8" width="2" height="2"/>
            <rect x="18" y="14" width="2" height="2"/>
            <rect x="24" y="14" width="2" height="2"/>
            <rect x="18" y="19.9996" width="2" height="2"/>
            <rect x="24" y="19.9996" width="2" height="2"/>
          </svg>
          Accounts
        </button>
        <button className={styles.tab} onClick={() => navigate('/payees')}>
          <svg width="24" height="24" viewBox="0 0 32 32" fill="currentColor">
            <polygon points="11.41 26.59 7.83 23 28 23 28 21 7.83 21 11.41 17.41 10 16 4 22 10 28 11.41 26.59"/>
            <polygon points="28 10 22 4 20.59 5.41 24.17 9 4 9 4 11 24.17 11 20.59 14.59 22 16 28 10"/>
          </svg>
          Pay &amp; Transfer
        </button>
        <button className={styles.tab} onClick={() => navigate('/dashboard')}>
          <svg width="24" height="24" viewBox="0 0 32 32" fill="currentColor">
            <path d="M26,2H8A2,2,0,0,0,6,4V8H4v2H6v5H4v2H6v5H4v2H6v4a2,2,0,0,0,2,2H26a2,2,0,0,0,2-2V4A2,2,0,0,0,26,2Zm0,26H8V24h2V22H8V17h2V15H8V10h2V8H8V4H26Z"/>
            <rect x="14" y="8" width="8" height="2"/>
            <rect x="14" y="15" width="8" height="2"/>
            <rect x="14" y="22" width="8" height="2"/>
          </svg>
          Dashboard
        </button>
      </nav>
    </div>
    </Theme>
  );
}
