import { useState, FormEvent } from 'react'
import { Invoice, SourceInteraction } from '../../types/customer'
import { PromiseCreateRequest } from '../../types/promise'
import { FailedConditionList } from './FailedConditionList'
import { usePromises } from '../../hooks/usePromises'

interface PromiseFormProps {
  customerId: string
  customerAccountId: string
  customerName: string
  invoices: Invoice[]
  interactions: SourceInteraction[]
  onSuccess: () => void
  onCancel: () => void
}

export function PromiseForm({
  customerAccountId,
  invoices,
  interactions,
  onSuccess,
  onCancel,
}: PromiseFormProps) {
  const [amount, setAmount] = useState('')
  const [date, setDate] = useState('')
  const [interactionId, setInteractionId] = useState('')
  const [note, setNote] = useState('')
  const [selectedInvoices, setSelectedInvoices] = useState<Set<string>>(new Set())

  const { createPromise, loading, policyFailure } = usePromises()

  const handleInvoiceToggle = (invoiceId: string) => {
    const newSelection = new Set(selectedInvoices)
    if (newSelection.has(invoiceId)) {
      newSelection.delete(invoiceId)
    } else {
      newSelection.add(invoiceId)
    }
    setSelectedInvoices(newSelection)
  }

  const calculateScopeTotal = () => {
    return invoices
      .filter((inv) => selectedInvoices.has(inv.invoice_id))
      .reduce((sum, inv) => sum + parseFloat(inv.open_amount), 0)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()

    const request: PromiseCreateRequest = {
      customer_account_id: customerAccountId,
      promised_amount: amount,
      currency_code: invoices[0]?.currency_code || 'USD',
      promised_date: new Date(date).toISOString(),
      promise_scope_type: 'invoice',
      scope_links: Array.from(selectedInvoices).map((invoiceId) => {
        const invoice = invoices.find((inv) => inv.invoice_id === invoiceId)
        return {
          link_type: 'invoice' as const,
          invoice_id: invoiceId,
          linked_amount: invoice?.open_amount || '0',
        }
      }),
      source_interaction_id: interactionId || undefined,
      note: note || undefined,
    }

    const idempotencyKey = `promise-${customerAccountId}-${Date.now()}`
    const result = await createPromise(request, idempotencyKey)

    if (result) {
      onSuccess()
    }
  }

  const scopeTotal = calculateScopeTotal()
  const hasAmountError = policyFailure?.failed_conditions.some((c) =>
    c.rule_code === 'PROMISE_AMOUNT_WITHIN_SCOPE'
  )
  const hasInteractionError = policyFailure?.failed_conditions.some((c) =>
    c.rule_code === 'PROMISE_SOURCE_REQUIRED'
  )

  return (
    <section className="bg-white border border-[#D5CDBB] rounded-md p-5 mb-6" aria-labelledby="form-title">
      <h2 id="form-title" className="text-lg font-bold text-[#14283A] font-serif mb-4">
        Promise details
      </h2>

      {policyFailure && <FailedConditionList policyFailure={policyFailure} />}

      <form onSubmit={handleSubmit}>
        <div className="flex gap-5 mb-4">
          <div className="flex-1">
            <label htmlFor="amount" className="block font-bold mb-1.5">
              Promised amount ({invoices[0]?.currency_code || 'USD'}) <span className="text-[#A4281A]" aria-hidden="true">*</span>
            </label>
            <input
              className={`w-full min-h-11 py-2 px-3 border rounded bg-white text-[#1B2A38] ${
                hasAmountError ? 'border-2 border-[#A4281A] bg-[#FFF8F7]' : 'border-[#7A858F]'
              }`}
              id="amount"
              name="amount"
              type="text"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              aria-describedby={hasAmountError ? 'amount-err' : undefined}
              aria-invalid={hasAmountError}
              required
            />
            {hasAmountError && (
              <div className="text-xs text-[#8E1F13] font-semibold mt-1" id="amount-err">
                Amount exceeds the selected invoice scope total of {invoices[0]?.currency_code || 'USD'} {scopeTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}.
              </div>
            )}
          </div>
          <div className="flex-1">
            <label htmlFor="date" className="block font-bold mb-1.5">
              Promised payment date <span className="text-[#A4281A]" aria-hidden="true">*</span>
            </label>
            <input
              className="w-full min-h-11 py-2 px-3 border border-[#7A858F] rounded bg-white text-[#1B2A38]"
              id="date"
              name="date"
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              required
            />
            <div className="text-xs text-[#47525C] mt-1">Format YYYY-MM-DD.</div>
          </div>
        </div>

        <div className="flex gap-5 mb-4">
          <div className="flex-1">
            <label htmlFor="interaction" className="block font-bold mb-1.5">
              Source interaction <span className="text-[#A4281A]" aria-hidden="true">*</span>
            </label>
            <select
              className={`w-full min-h-11 py-2 px-3 border rounded bg-white text-[#1B2A38] ${
                hasInteractionError ? 'border-2 border-[#A4281A] bg-[#FFF8F7]' : 'border-[#7A858F]'
              }`}
              id="interaction"
              name="interaction"
              value={interactionId}
              onChange={(e) => setInteractionId(e.target.value)}
              aria-describedby={hasInteractionError ? 'int-err' : undefined}
              aria-invalid={hasInteractionError}
              required
            >
              <option value="">Select the call, email or meeting where the customer committed</option>
              {interactions.map((int) => (
                <option key={int.interaction_id} value={int.interaction_id}>
                  {int.interaction_type.charAt(0).toUpperCase() + int.interaction_type.slice(1)},{' '}
                  {new Date(int.occurred_at).toLocaleDateString('en-GB', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                  })}{' '}
                  ({int.interaction_id})
                </option>
              ))}
            </select>
            {hasInteractionError && (
              <div className="text-xs text-[#8E1F13] font-semibold mt-1" id="int-err">
                Select the interaction in which the customer made this commitment.
              </div>
            )}
          </div>
          <div className="flex-1">
            <label htmlFor="note" className="block font-bold mb-1.5">
              Interaction note
            </label>
            <textarea
              className="w-full min-h-18 py-2 px-3 border border-[#7A858F] rounded bg-white text-[#1B2A38]"
              id="note"
              name="note"
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
        </div>

        <fieldset className="border border-[#D5CDBB] rounded py-3 px-4 m-0 mb-5">
          <legend className="font-bold px-1.5">
            Scope: invoices covered by this promise <span className="text-[#A4281A]" aria-hidden="true">*</span>
          </legend>
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th scope="col" className="text-left text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
                  Select
                </th>
                <th scope="col" className="text-left text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
                  Invoice
                </th>
                <th scope="col" className="text-left text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
                  Due date
                </th>
                <th scope="col" className="text-right text-xs tracking-wider uppercase text-[#47525C] py-2 px-2.5 border-b-2 border-[#14283A]">
                  Open amount ({invoices[0]?.currency_code || 'USD'})
                </th>
              </tr>
            </thead>
            <tbody>
              {invoices.map((invoice) => (
                <tr key={invoice.invoice_id}>
                  <td className="py-2.5 px-2.5 border-b border-[#E4DECF] align-middle">
                    <input
                      type="checkbox"
                      id={`inv-${invoice.invoice_id}`}
                      name={`inv-${invoice.invoice_id}`}
                      checked={selectedInvoices.has(invoice.invoice_id)}
                      onChange={() => handleInvoiceToggle(invoice.invoice_id)}
                      aria-label={`Select invoice ${invoice.invoice_number}`}
                    />
                  </td>
                  <td className="py-2.5 px-2.5 border-b border-[#E4DECF] align-middle">{invoice.invoice_number}</td>
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
                </tr>
              ))}
            </tbody>
          </table>
          <div className="text-xs text-[#47525C] mt-2">
            Selected scope total: {invoices[0]?.currency_code || 'USD'} {scopeTotal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}. You can also choose the whole account balance instead of specific invoices.
          </div>
        </fieldset>

        <div className="flex gap-3 mt-5">
          <button
            className="inline-block min-h-11 py-2.5 px-4 rounded font-bold border-2 border-[#14283A] bg-[#14283A] text-white"
            type="submit"
            disabled={loading}
          >
            {loading ? 'Saving...' : 'Save promise'}
          </button>
          <button
            className="inline-block min-h-11 py-2.5 px-4 rounded font-bold border-2 border-[#14283A] bg-white text-[#14283A]"
            type="button"
            onClick={onCancel}
          >
            Cancel
          </button>
        </div>
      </form>
    </section>
  )
}
