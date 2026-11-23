import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../lib/auth-context';
import { apiClient, ApiError } from '../lib/api-client';
import { AccountCard } from '../components/accounts/AccountCard';
import { CapabilityBanner } from '../components/shared/CapabilityBanner';

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

interface CapabilityStatus {
  capability_name: string;
  status_value: 'healthy' | 'stale' | 'partial' | 'unavailable' | 'restricted';
  customer_message_code: string | null;
  customer_message: string;
  recovery_guidance: string;
  effective_from: string;
}

interface AccountsResponse {
  items: AccountItem[];
  total: number;
  page: number;
  page_size: number;
  overview_state: 'complete' | 'partial' | 'unavailable';
  capability: CapabilityStatus;
}

interface CapabilityStatusesResponse {
  items: CapabilityStatus[];
  total: number;
  page: number;
  page_size: number;
}

export function AccountsOverviewPage() {
  const { logout, user } = useAuth();
  const location = useLocation();
  const [accounts, setAccounts] = useState<AccountItem[]>([]);
  const [overviewState, setOverviewState] = useState<'complete' | 'partial' | 'unavailable'>('complete');
  const [capability, setCapability] = useState<CapabilityStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAccounts();
  }, []);

  const fetchAccounts = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Fetch accounts
      const accountsResponse = await apiClient.get<AccountsResponse>('/v1/accounts/');
      setAccounts(accountsResponse.items);
      setOverviewState(accountsResponse.overview_state);
      setCapability(accountsResponse.capability);

    } catch (err) {
      console.error('Failed to fetch accounts:', err);
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError('Failed to load accounts. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const getCapabilityBannerMessage = (): { variant: 'partial' | 'unavailable' | 'stale'; message: string } | null => {
    if (overviewState === 'unavailable') {
      return {
        variant: 'unavailable',
        message: '<strong>We can\'t show every account</strong>One account could not be confirmed, so it is marked below. Your other accounts are shown as normal.',
      };
    }
    
    if (overviewState === 'partial') {
      return {
        variant: 'unavailable',
        message: '<strong>We can\'t show every account</strong>One account could not be confirmed, so it is marked below. Your other accounts are shown as normal.',
      };
    }

    // Check if any account has stale balance
    const hasStaleBalance = accounts.some(acc => acc.balance.availability_state === 'stale');
    if (hasStaleBalance) {
      return {
        variant: 'stale',
        message: '<strong>Some balances are not current</strong>We are showing the last information we have. Check the time on each account before you rely on it.',
      };
    }

    return null;
  };

  const bannerInfo = getCapabilityBannerMessage();

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-[#002563] text-white">
        <span>9:41</span>
      </div>

      {/* Header */}
      <div className="flex justify-between items-center px-4 py-2 bg-[#002563] text-white">
        <span className="font-bold text-lg">Your Bank</span>
        <button
          onClick={handleLogout}
          className="inline-flex items-center min-h-11 min-w-11 text-white font-bold underline"
        >
          Sign out
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4">
        <h1 className="text-[28px] leading-tight font-bold text-[#002563] mb-0">Your accounts</h1>
        <p className="text-base text-[#575756] m-0">Hello, {user?.display_name || 'Customer'}</p>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0074CD]"></div>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && (
          <div className="flex gap-3 p-4 rounded-lg border-2 border-[#BE222A] bg-white" role="alert">
            <svg className="w-5 h-5 flex-shrink-0 text-[#BE222A]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3l10 18H2z" />
              <path d="M12 10v5M12 18v.5" />
            </svg>
            <div>
              <strong className="block font-bold">Failed to load accounts</strong>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Capability banner */}
        {!isLoading && !error && bannerInfo && (
          <CapabilityBanner variant={bannerInfo.variant} message={bannerInfo.message} />
        )}

        {/* Accounts list */}
        {!isLoading && !error && accounts.length > 0 && (
          <ul className="list-none m-0 p-0 flex flex-col gap-4">
            {accounts.map((account) => (
              <li key={account.account_id}>
                <AccountCard account={account} />
              </li>
            ))}
          </ul>
        )}

        {/* Empty state */}
        {!isLoading && !error && accounts.length === 0 && (
          <div className="text-center py-8 text-[#4F5155]">
            <p>No accounts to display.</p>
          </div>
        )}

        {/* Refresh button */}
        {!isLoading && !error && (
          <button
            onClick={fetchAccounts}
            className="flex items-center justify-center min-h-12 px-6 font-bold text-[#0074CD] bg-white border-2 border-[#0074CD] rounded-lg"
          >
            Refresh accounts
          </button>
        )}

        {/* Footer note */}
        {!isLoading && !error && (
          <p className="text-sm text-[#4F5155] m-0">
            Freshness stays on screen when you refresh. Read from the account read model, not a live bank call.
          </p>
        )}
      </div>

      {/* Bottom tabs */}
      <nav className="flex bg-white border-t border-[#E0E0E0]" aria-label="Main">
        <Link
          to="/accounts"
          aria-current={location.pathname === '/accounts' ? 'page' : undefined}
          className="flex-1 min-h-14 flex items-center justify-center text-xs font-bold text-[#0074CD] border-t-[3px] border-[#0074CD]"
        >
          Accounts
        </Link>
        <Link
          to="/payees"
          aria-current={location.pathname.startsWith('/payees') || location.pathname.startsWith('/payment') ? 'page' : undefined}
          className={`flex-1 min-h-14 flex items-center justify-center text-xs font-bold ${
            location.pathname.startsWith('/payees') || location.pathname.startsWith('/payment')
              ? 'text-[#0074CD] border-t-[3px] border-[#0074CD]'
              : 'text-[#4F5155]'
          }`}
        >
          Pay &amp; Transfer
        </Link>
      </nav>
    </div>
  );
}
