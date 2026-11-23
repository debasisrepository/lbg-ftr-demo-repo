import { BadgeIcon } from '../shared/BadgeIcon';

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

interface AccountCardProps {
  account: AccountItem;
}

export function AccountCard({ account }: AccountCardProps) {
  const { balance, freshness_status, freshness_text, display_name, masked_account_identifier, item_state } = account;
  
  // Determine badge variant from balance availability state
  const getBadgeVariant = (): 'current' | 'stale' | 'unavailable' => {
    if (balance.availability_state === 'current') return 'current';
    if (balance.availability_state === 'stale') return 'stale';
    return 'unavailable';
  };

  // Determine badge text from freshness and availability
  const getBadgeText = (): string => {
    if (balance.availability_state === 'current') return 'Current';
    if (balance.availability_state === 'stale') return 'May be out of date';
    if (item_state === 'partial') return 'Partly available';
    return 'Unavailable';
  };

  // Balance display
  const balanceDisplay = balance.availability_state === 'current' || balance.availability_state === 'stale'
    ? balance.display_text
    : balance.display_text;

  const balanceClassName = balance.availability_state === 'unavailable' || balance.availability_state === 'unknown'
    ? 'text-xl font-bold text-[#002563] my-3 balance-amount'
    : 'text-[32px] leading-tight font-bold text-black my-3 balance-amount';

  // Freshness text display
  const getFreshnessText = (): string => {
    if (item_state === 'partial') {
      return 'Not current. This account cannot be used to pay from right now.';
    }
    if (balance.availability_state === 'stale') {
      return `Balance may be out of date. ${freshness_text}`;
    }
    if (balance.availability_state === 'unavailable' || balance.availability_state === 'unknown') {
      return 'Not current. We could not confirm this balance.';
    }
    return freshness_text;
  };

  return (
    <article
      className="block bg-white rounded-2xl shadow-md p-4"
      aria-labelledby={`account-${account.account_id}`}
    >
      <h4 id={`account-${account.account_id}`} className="text-lg font-bold text-[#002563] m-0">
        {display_name}
      </h4>
      <p className="text-base text-[#4F5155] m-0">Account ending {masked_account_identifier}</p>
      
      <p className={balanceClassName}>{balanceDisplay}</p>
      
      <div className="flex items-center gap-2 mt-2 flex-wrap freshness-badge">
        <BadgeIcon variant={getBadgeVariant()} text={getBadgeText()} />
      </div>
      
      <p className="text-sm text-[#4F5155] mt-1 mb-0 freshness-time">{getFreshnessText()}</p>
    </article>
  );
}
