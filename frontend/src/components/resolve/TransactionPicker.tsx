interface Transaction {
  id: string;
  merchant_name: string;
  amount: number;
  date: string;
  card_last_four: string;
  status?: string;
}

interface TransactionPickerProps {
  transactions: Transaction[];
  selectedId?: string;
  onSelect: (id: string) => void;
}

export function TransactionPicker({ transactions, selectedId, onSelect }: TransactionPickerProps) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="font-bold text-base mb-1">Or start from something you can see</legend>
      <p className="text-[14px] text-[#4A5A60]">Pick a payment and we'll attach it for you. Optional.</p>
      
      {transactions.map((txn) => {
        const isSelected = txn.id === selectedId;
        return (
          <label 
            key={txn.id}
            className={`flex items-center gap-3 min-h-[64px] p-3 md:p-4 rounded-xl cursor-pointer ${
              isSelected 
                ? 'border-2 border-[#0B5D5B] bg-[#E0EFEE]' 
                : 'border border-[#D5CFC0] bg-white'
            } focus-within:outline focus-within:outline-3 focus-within:outline-[#1F6FEB] focus-within:outline-offset-2`}
            htmlFor={`txn-${txn.id}`}
          >
            <input 
              type="radio" 
              name="txn" 
              id={`txn-${txn.id}`}
              checked={isSelected}
              onChange={() => onSelect(txn.id)}
              className="w-[22px] h-[22px] accent-[#0B5D5B] flex-shrink-0 m-0"
            />
            <span className="flex-1 flex flex-col">
              <span className="font-semibold">{txn.merchant_name}</span>
              <span className="text-[14px] text-[#4A5A60]">{txn.date} · Card ending {txn.card_last_four}</span>
              {txn.status && (
                <span className="mt-1">
                  <span className="inline-flex items-center gap-1 text-[13px] font-semibold px-2 py-[2px] rounded-[10px] bg-[#FFF0C7] text-[#5B3A00]">
                    <svg className="w-[14px] h-[14px] fill-none stroke-current stroke-2" viewBox="0 0 24 24" aria-hidden="true">
                      <circle cx="12" cy="12" r="10" strokeLinecap="round" strokeLinejoin="round"/>
                      <polyline points="12 6 12 12 16 14" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                    {txn.status}
                  </span>
                </span>
              )}
            </span>
            <span className="font-bold tabular-nums">£{txn.amount.toFixed(2)}</span>
          </label>
        );
      })}
    </fieldset>
  );
}
