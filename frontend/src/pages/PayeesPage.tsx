import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { InlineNotification, Button, TextInput, Theme } from '@carbon/react';
import { Checkmark, Add } from '@carbon/icons-react';
import apiClient from '../lib/api-client';
import { useAuth } from '../lib/auth-context';
import type { PayeesResponse, Payee, CreatePayeeRequest, CreatePayeeResponse } from '../types';
import styles from './PayeesPage.module.scss';

export default function PayeesPage() {
  const navigate = useNavigate();
  const { activeProfileId } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [payees, setPayees] = useState<Payee[]>([]);
  const [selectedPayeeId, setSelectedPayeeId] = useState<number | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [copResult, setCopResult] = useState<CreatePayeeResponse | null>(null);
  const [confirmWarning, setConfirmWarning] = useState(false);
  
  // New payee form state
  const [displayName, setDisplayName] = useState('');
  const [sortCode, setSortCode] = useState('');
  const [accountNumber, setAccountNumber] = useState('');

  useEffect(() => {
    async function fetchPayees() {
      try {
        setLoading(true);
        setError(null);
        
        if (!activeProfileId) {
          setError('No active profile available');
          setLoading(false);
          return;
        }
        
        const response = await apiClient.get<PayeesResponse>(`/payees?profile_id=${activeProfileId}`);
        setPayees(response.payees || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load payees');
      } finally {
        setLoading(false);
      }
    }

    fetchPayees();
  }, [activeProfileId]);

  const handleSelectPayee = (payeeId: number) => {
    setSelectedPayeeId(payeeId);
    setCopResult(null);
    setConfirmWarning(false);
  };

  const handleAddPayee = () => {
    setShowAddForm(true);
    setSelectedPayeeId(null);
    setCopResult(null);
    setConfirmWarning(false);
  };

  const handleCheckPayee = async () => {
    // This would require fresh SCA verification
    // For now, simulate the CoP check
    try {
      setError(null);
      // In real implementation, would need to:
      // 1. Request fresh payee-action SCA challenge
      // 2. Show SCA verification UI
      // 3. Call POST /payees with challenge ID and assertion
      
      // Simulated response for demo
      const mockResponse: CreatePayeeResponse = {
        payee_id: Date.now(),
        display_name: displayName,
        sort_code: sortCode,
        masked_account_number: `****${accountNumber.slice(-4)}`,
        cop_result: 'match',
        warning_message: undefined,
        can_proceed: true,
        override_required: false,
      };
      
      setCopResult(mockResponse);
      
      // If match, add to payees list
      if (mockResponse.cop_result === 'match') {
        const newPayee: Payee = {
          payee_id: mockResponse.payee_id,
          display_name: mockResponse.display_name,
          sort_code: mockResponse.sort_code,
          masked_account_number: mockResponse.masked_account_number,
          can_proceed: mockResponse.can_proceed,
          latest_cop_result: mockResponse.cop_result,
        };
        setPayees([...payees, newPayee]);
        setSelectedPayeeId(newPayee.payee_id);
        setShowAddForm(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check payee');
    }
  };

  const handleContinue = () => {
    if (selectedPayeeId || (copResult && copResult.can_proceed)) {
      const payee = selectedPayeeId 
        ? payees.find(p => p.payee_id === selectedPayeeId)
        : copResult 
        ? {
            payee_id: copResult.payee_id,
            display_name: copResult.display_name,
            sort_code: copResult.sort_code,
            masked_account_number: copResult.masked_account_number,
            can_proceed: copResult.can_proceed,
            latest_cop_result: copResult.cop_result,
          }
        : null;

      if (payee) {
        // Navigate to payment entry with payee data
        // In real implementation, would also fetch account data
        // For now, using seed account data (account_id: 2)
        navigate('/payment/entry', { 
          state: { 
            payee,
            account: {
              account_id: 2,
              account_name: 'Current Account',
              sort_code: '00-03-20',
              masked_account_number: '****5920',
              available_balance_minor: 124836,
              current_balance_minor: 124836,
              currency: 'GBP',
              account_type: 'current_account',
              freshness_state: 'current',
              last_updated_at: new Date().toISOString(),
            }
          } 
        });
      }
    }
  };

  const canContinue = selectedPayeeId !== null || (copResult?.can_proceed && (copResult.cop_result === 'match' || confirmWarning));

  if (loading) {
    return (
      <Theme theme="white">
        <div className={styles.container}>
          <p>Loading payees...</p>
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
            title="Error loading payees"
            subtitle={error}
            lowContrast
          />
        </div>
      </Theme>
    );
  }

  return (
    <Theme theme="white">
      <div className={styles.container}>
      <main className={styles.content}>
        <h1 className={styles.title}>Pay &amp; Transfer</h1>
        <p className={styles.lead}>Who do you want to pay?</p>

        {!showAddForm && (
          <>
            <div role="radiogroup" aria-label="Saved payees" className={styles.payeeList}>
              {payees.map((payee) => (
                <button
                  key={payee.payee_id}
                  className={styles.payeeTile}
                  role="radio"
                  aria-checked={selectedPayeeId === payee.payee_id}
                  onClick={() => handleSelectPayee(payee.payee_id)}
                  type="button"
                >
                  <span className={styles.who}>
                    <span className={styles.name}>{payee.display_name}</span>
                    <span className={styles.account}>
                      {payee.sort_code} · {payee.masked_account_number}
                    </span>
                  </span>
                  <span className={`${styles.mark} ${selectedPayeeId === payee.payee_id ? styles.markChecked : ''}`}>
                    {selectedPayeeId === payee.payee_id && <Checkmark size={20} />}
                  </span>
                </button>
              ))}
            </div>

            <button className={styles.addButton} type="button" onClick={handleAddPayee}>
              <Add size={24} />
              Add a new payee
            </button>
          </>
        )}

        {showAddForm && (
          <div className={styles.form}>
            <InlineNotification
              kind="info"
              title="Fresh verification required"
              subtitle="Confirm it's you before adding this payee."
              lowContrast
            />
            
            <TextInput
              id="payee-name"
              labelText="Name on the account"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
            
            <div className={styles.split}>
              <TextInput
                id="sort-code"
                labelText="Sort code"
                value={sortCode}
                onChange={(e) => setSortCode(e.target.value)}
                placeholder="00-00-00"
              />
              <TextInput
                id="account-number"
                labelText="Account number"
                value={accountNumber}
                onChange={(e) => setAccountNumber(e.target.value)}
                placeholder="12345678"
              />
            </div>
            
            <Button onClick={handleCheckPayee} disabled={!displayName || !sortCode || !accountNumber}>
              Check payee
            </Button>
          </div>
        )}

        {copResult && copResult.cop_result === 'match' && (
          <InlineNotification
            kind="success"
            title="Name matches"
            subtitle={`The account name matches ${copResult.display_name}. You can continue without re-entering any details.`}
            lowContrast
          />
        )}

        {copResult && copResult.cop_result === 'close_match' && (
          <>
            <InlineNotification
              kind="warning"
              title="The name is a close match"
              subtitle={copResult.warning_message || "Check the details with the payee before you continue."}
              lowContrast
            />
            <label className={styles.checkboxRow}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={confirmWarning}
                onChange={(e) => setConfirmWarning(e.target.checked)}
              />
              <span>I've checked the details and want to continue with this payee.</span>
            </label>
          </>
        )}

        {copResult && copResult.cop_result === 'no_match' && (
          <>
            <InlineNotification
              kind="error"
              title="The name doesn't match"
              subtitle="The account isn't registered to this name. If you pay it, you may not get your money back. Check with the payee first."
              lowContrast
            />
            <label className={styles.checkboxRow}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={confirmWarning}
                onChange={(e) => setConfirmWarning(e.target.checked)}
              />
              <span>I understand the name doesn't match and still want to continue.</span>
            </label>
          </>
        )}

        {copResult && copResult.cop_result === 'unavailable' && (
          <>
            <InlineNotification
              kind="warning"
              title="We couldn't check this name"
              subtitle="The name check isn't available right now. You can try again, or continue at your own risk."
              lowContrast
            />
            <label className={styles.checkboxRow}>
              <input
                type="checkbox"
                className={styles.checkbox}
                checked={confirmWarning}
                onChange={(e) => setConfirmWarning(e.target.checked)}
              />
              <span>I want to continue without a name check.</span>
            </label>
          </>
        )}

        <button
          className={`${styles.continueButton} ${!canContinue ? styles.disabled : ''}`}
          type="button"
          onClick={handleContinue}
          disabled={!canContinue}
          aria-disabled={!canContinue}
        >
          <span>Continue to payment</span>
          <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
            <polygon points="11,8 6,13 5.3,12.3 9.6,8 5.3,3.7 6,3"/>
          </svg>
        </button>
      </main>

      <nav className={styles.tabBar}>
        <button className={styles.tab} onClick={() => navigate('/accounts')}>
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
        <button className={`${styles.tab} ${styles.tabActive}`} onClick={() => navigate('/payees')}>
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
