interface PayeeItem {
  payee_id: string;
  payee_name: string;
  payee_sort_code: string;
  masked_account_identifier: string;
}

interface PayeeListItemProps {
  payee: PayeeItem;
  onSelect: () => void;
}

export function PayeeListItem({ payee, onSelect }: PayeeListItemProps) {
  // Get initials from payee name (first letter of first and last word)
  const getInitials = (name: string): string => {
    const words = name.trim().split(/\s+/);
    if (words.length === 1) {
      return words[0].substring(0, 2).toUpperCase();
    }
    return (words[0][0] + words[words.length - 1][0]).toUpperCase();
  };

  return (
    <button
      type="button"
      onClick={onSelect}
      data-testid="payee-item"
      className="flex items-center gap-3 w-full min-h-16 py-2 px-0 bg-white border-0 cursor-pointer text-left"
    >
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-[#F2FAFF] text-[#002563] flex items-center justify-center font-bold" aria-hidden="true">
        {getInitials(payee.payee_name)}
      </div>
      <div className="flex-1">
        <div className="block font-bold text-black">{payee.payee_name}</div>
        <div className="block text-sm text-[#4F5155]">
          Sort code {payee.payee_sort_code}, account ending {payee.masked_account_identifier}
        </div>
      </div>
      <svg className="w-5 h-5 flex-shrink-0 text-[#0074CD]" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" viewBox="0 0 24 24" aria-hidden="true">
        <path d="M9 5l7 7-7 7" />
      </svg>
    </button>
  );
}
