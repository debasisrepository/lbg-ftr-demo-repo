interface AccountContextCardProps {
  overdueBalance: string
  currencyCode: string
  oldestOverdueDays: number
  queueState: string
  openPromisesCount: number
}

export function AccountContextCard({
  overdueBalance,
  currencyCode,
  oldestOverdueDays,
  queueState,
  openPromisesCount,
}: AccountContextCardProps) {
  return (
    <section className="bg-white border border-[#D5CDBB] rounded-md p-5 mb-6" aria-labelledby="ctx-title">
      <h2 id="ctx-title" className="text-lg font-bold text-[#14283A] font-serif mb-4">
        Account context
      </h2>
      <div className="m-0">
        <div className="py-1.5 border-b border-[#E4DECF]">
          <div className="text-xs tracking-wider uppercase text-[#47525C]">Overdue balance</div>
          <div className="font-semibold">{currencyCode} {parseFloat(overdueBalance).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
        </div>
        <div className="py-1.5 border-b border-[#E4DECF]">
          <div className="text-xs tracking-wider uppercase text-[#47525C]">Oldest overdue item</div>
          <div className="font-semibold">{oldestOverdueDays} days</div>
        </div>
        <div className="py-1.5 border-b border-[#E4DECF]">
          <div className="text-xs tracking-wider uppercase text-[#47525C]">Queue state</div>
          <div className="font-semibold">
            <span className="inline-block py-0.5 px-2.5 rounded-xl text-xs font-semibold border bg-[#E3F1EC] text-[#0F5B46] border-[#7DB8A5]">
              {queueState}
            </span>
          </div>
        </div>
        <div className="py-1.5">
          <div className="text-xs tracking-wider uppercase text-[#47525C]">Open promises</div>
          <div className="font-semibold">{openPromisesCount > 0 ? openPromisesCount : 'None'}</div>
        </div>
      </div>
    </section>
  )
}
