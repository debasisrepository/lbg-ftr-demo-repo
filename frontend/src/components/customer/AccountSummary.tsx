import { CustomerAccount } from '../../types/customer'

interface AccountSummaryProps {
  account: CustomerAccount
  overdueBalance: string
  oldestOverdueDays: number
  paymentTerms: string
  creditLimit: string | null
  queueState: string
  isSensitiveUser: boolean
}

export function AccountSummary({
  account,
  overdueBalance,
  oldestOverdueDays,
  paymentTerms,
  creditLimit,
  queueState,
  isSensitiveUser,
}: AccountSummaryProps) {
  return (
    <div className="flex flex-wrap m-0">
      <div className="w-1/2 py-1.5">
        <div className="text-xs tracking-wider uppercase text-[#47525C]">Total open balance</div>
        <div className="font-semibold">{account.currency_code} {parseFloat(account.open_balance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      </div>
      <div className="w-1/2 py-1.5">
        <div className="text-xs tracking-wider uppercase text-[#47525C]">Overdue balance</div>
        <div className="font-semibold">{account.currency_code} {parseFloat(overdueBalance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
      </div>
      <div className="w-1/2 py-1.5">
        <div className="text-xs tracking-wider uppercase text-[#47525C]">Oldest overdue item</div>
        <div className="font-semibold">{oldestOverdueDays} days</div>
      </div>
      <div className="w-1/2 py-1.5">
        <div className="text-xs tracking-wider uppercase text-[#47525C]">Payment terms</div>
        <div className="font-semibold">{paymentTerms}</div>
      </div>
      <div className="w-1/2 py-1.5">
        <div className="text-xs tracking-wider uppercase text-[#47525C]">Credit limit</div>
        <div className="font-semibold">
          {isSensitiveUser && creditLimit ? (
            `${account.currency_code} ${parseFloat(creditLimit).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
          ) : (
            <>
              <span
                className="tracking-widest bg-[#E4DECF] py-0.5 px-2.5 rounded font-bold"
                aria-label="Masked field, permission required"
              >
                &#9679;&#9679;&#9679;&#9679;&#9679;&#9679;
              </span>{' '}
              <span className="text-[#47525C] text-xs">Masked for your role</span>
            </>
          )}
        </div>
      </div>
      <div className="w-1/2 py-1.5">
        <div className="text-xs tracking-wider uppercase text-[#47525C]">Queue state</div>
        <div className="font-semibold">
          <span className="inline-block py-0.5 px-2.5 rounded-xl text-xs font-semibold border bg-[#E3F1EC] text-[#0F5B46] border-[#7DB8A5]">
            {queueState}
          </span>
        </div>
      </div>
    </div>
  )
}
