import { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../lib/auth-context';
import { apiClient, ApiError } from '../lib/api-client';
import { PayeeListItem } from '../components/payments/PayeeListItem';

interface PayeeItem {
  payee_id: string;
  payee_name: string;
  payee_sort_code: string;
  masked_account_identifier: string;
}

interface CapabilityStatus {
  capability_name: string;
  status_value: 'healthy' | 'stale' | 'partial' | 'unavailable' | 'restricted';
  customer_message_code: string | null;
  customer_message: string;
  recovery_guidance: string;
  effective_from: string;
}

interface PayeesResponse {
  items: PayeeItem[];
  total: number;
  page: number;
  page_size: number;
  capability: CapabilityStatus;
}

interface CapabilityStatusesResponse {
  items: CapabilityStatus[];
  total: number;
  page: number;
  page_size: number;
}

export function PayeesPage() {
  const { logout, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [payees, setPayees] = useState<PayeeItem[]>([]);
  const [capability, setCapability] = useState<CapabilityStatus | null>(null);
  const [paymentsCapability, setPaymentsCapability] = useState<CapabilityStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPayees();
    fetchCapabilityStatuses();
  }, []);

  const fetchPayees = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<PayeesResponse>('/v1/payees');
      setPayees(response.items);
      setCapability(response.capability);
    } catch (err) {
      console.error('Failed to fetch payees:', err);
      if (err instanceof ApiError) {
        setError(err.detail || err.message);
      } else {
        setError('Failed to load payees. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCapabilityStatuses = async () => {
    try {
      const response = await apiClient.get<CapabilityStatusesResponse>('/v1/capability-statuses/');
      const paymentsStatus = response.items.find(c => c.capability_name === 'payments');
      if (paymentsStatus) {
        setPaymentsCapability(paymentsStatus);
      }
    } catch (err) {
      console.error('Failed to fetch capability statuses:', err);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const handlePayeeSelect = (payee: PayeeItem) => {
    navigate('/payment-entry', { state: { payee } });
  };

  const handleTryAgain = () => {
    fetchPayees();
    fetchCapabilityStatuses();
  };

  const isPayeesUnavailable = capability?.status_value === 'unavailable';
  const isPaymentsUnavailable = paymentsCapability?.status_value === 'unavailable';

  return (
    <div className="min-h-screen flex flex-col bg-[#F7F9F8]">
      {/* Status bar */}
      <div className="h-11 flex items-center px-6 text-sm font-bold bg-white text-black">
        <span>9:41</span>
      </div>

      {/* Content */}
      <div className="flex-1 flex flex-col gap-4 p-4 pb-6">
        <h1 className="text-[28px] leading-tight font-bold text-[#002563] m-0">Pay &amp; Transfer</h1>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#0074CD]" role="status"></div>
          </div>
        )}

        {/* Payees unavailable banner */}
        {!isLoading && isPayeesUnavailable && (
          <>
            <div className="flex gap-3 p-4 rounded-lg border-2 border-[#BE222A] bg-white" role="status">
              <svg className="w-5 h-5 flex-shrink-0 text-[#BE222A]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3l10 18H2z" />
                <path d="M12 10v5M12 18v.5" />
              </svg>
              <div>
                <strong className="block font-bold">Your saved payees aren't available right now</strong>
                <span>We can't show your payees at the moment. Your accounts are not affected. Try again later.</span>
              </div>
            </div>
            <button
              onClick={handleTryAgain}
              className="flex items-center justify-center min-h-12 px-6 font-bold text-white bg-[#0074CD] border-2 border-[#0074CD] rounded-lg"
            >
              Try again
            </button>
          </>
        )}

        {/* Payments unavailable banner */}
        {!isLoading && isPaymentsUnavailable && (
          <div className="flex gap-3 p-4 rounded-lg border-2 border-[#BE222A] bg-white" role="status">
            <svg className="w-5 h-5 flex-shrink-0 text-[#BE222A]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3l10 18H2z" />
              <path d="M12 10v5M12 18v.5" />
            </svg>
            <div>
              <strong className="block font-bold">New payments are paused</strong>
              <span>We can't send new payments right now, so nothing can be started. You can still see your accounts. Any payment you already started keeps its status.</span>
            </div>
          </div>
        )}

        {/* Payees list */}
        {!isLoading && !isPayeesUnavailable && !isPaymentsUnavailable && payees.length > 0 && (
          <>
            <h2 className="text-sm font-bold uppercase tracking-wider text-[#4F5155] mt-2 mb-0">Pay someone</h2>
            <ul className="list-none m-0 p-0 border-t border-[#E0E0E0]">
              {payees.map((payee) => (
                <li key={payee.payee_id} className="border-b border-[#E0E0E0]">
                  <PayeeListItem payee={payee} onSelect={() => handlePayeeSelect(payee)} />
                </li>
              ))}
            </ul>
            <p className="text-sm text-[#4F5155] m-0">
              Choose a payee to start a payment. Full account numbers are never shown.
            </p>
          </>
        )}

        {/* Empty state */}
        {!isLoading && !isPayeesUnavailable && !isPaymentsUnavailable && payees.length === 0 && !error && (
          <div className="text-center py-8 text-[#4F5155]">
            <p>No saved payees available.</p>
          </div>
        )}

        {/* Error state */}
        {error && !isLoading && !isPayeesUnavailable && (
          <div className="flex gap-3 p-4 rounded-lg border-2 border-[#BE222A] bg-white" role="alert">
            <svg className="w-5 h-5 flex-shrink-0 text-[#BE222A]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 3l10 18H2z" />
              <path d="M12 10v5M12 18v.5" />
            </svg>
            <div>
              <strong className="block font-bold">Failed to load payees</strong>
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Bottom tabs */}
      <nav className="flex bg-white border-t border-[#E0E0E0]" aria-label="Main">
        <Link
          to="/accounts"
          aria-current={location.pathname === '/accounts' ? 'page' : undefined}
          className="flex-1 min-h-14 flex items-center justify-center text-xs font-bold text-[#4F5155]"
        >
          Accounts
        </Link>
        <Link
          to="/payees"
          aria-current={location.pathname === '/payees' ? 'page' : undefined}
          className="flex-1 min-h-14 flex items-center justify-center text-xs font-bold text-[#0074CD] border-t-[3px] border-[#0074CD]"
        >
          Pay &amp; Transfer
        </Link>
      </nav>
    </div>
  );
}
