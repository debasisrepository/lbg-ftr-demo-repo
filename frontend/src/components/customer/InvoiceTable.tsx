import { Invoice } from '../../types/customer'

interface InvoiceTableProps {
  invoices: Invoice[]
}

export function InvoiceTable({ invoices }: InvoiceTableProps) {
  if (invoices.length === 0) {
    return <p className="text-[#47525C]">No overdue invoices.</p>
  }

  return (
    <table className="w-full border-collapse">
      <thead>
        <tr>
          <th scope="col" className="text-left text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
            Invoice
          </th>
          <th scope="col" className="text-left text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
            Due date
          </th>
          <th scope="col" className="text-right text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
            Amount ({invoices[0]?.currency_code || 'USD'})
          </th>
          <th scope="col" className="text-right text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
            Days overdue
          </th>
          <th scope="col" className="text-left text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
            Flag
          </th>
        </tr>
      </thead>
      <tbody>
        {invoices.map((invoice) => (
          <tr key={invoice.invoice_id}>
            <td className="py-2.5 px-2.5 border-b border-[#E4DECF] align-middle">
              {invoice.invoice_number}
            </td>
            <td className="py-2.5 px-2.5 border-b border-[#E4DECF] align-middle">
              {new Date(invoice.due_date).toLocaleDateString('en-GB', {
                day: '2-digit',
                month: 'short',
                year: 'numeric',
              })}
            </td>
            <td className="py-2.5 px-2.5 border-b border-[#E4DECF] align-middle text-right">
              {parseFloat(invoice.open_amount).toLocaleString('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2,
              })}
            </td>
            <td className="py-2.5 px-2.5 border-b border-[#E4DECF] align-middle text-right">
              {invoice.days_past_due ?? 0}
            </td>
            <td className="py-2.5 px-2.5 border-b border-[#E4DECF] align-middle">
              <span className="inline-block py-0.5 px-2.5 rounded-xl text-xs font-semibold border bg-[#EEEEEE] text-[#3C444B] border-[#9AA2A8]">
                None
              </span>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
