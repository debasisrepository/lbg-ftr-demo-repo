import { useParams, useNavigate, Link } from 'react-router-dom'
import { useCustomerView } from '../hooks/useCustomerView'
import { SectionCard } from '../components/customer/SectionCard'
import { AccountSummary } from '../components/customer/AccountSummary'
import { InvoiceTable } from '../components/customer/InvoiceTable'
import { useAuth } from '../lib/use-auth'

export function Customer360Page() {
  const { customerId } = useParams<{ customerId: string }>()
  const navigate = useNavigate()
  const { activeRole } = useAuth()
  const { data, loading, error } = useCustomerView(customerId)

  if (loading) {
    return (
      <div className="p-8">
        <div className="text-[#47525C]">Loading customer view...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="text-[#8E1F13]">Error: {error}</div>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="p-8">
        <div className="text-[#47525C]">No customer data available.</div>
      </div>
    )
  }

  const profile = data.profile.data
  const accounts = data.accounts.data?.[0]
  const invoices = data.invoices.data || []
  const promises = data.promises.data || []
  const interactions = data.source_interactions.data || []
  
  const isSensitiveUser = activeRole?.can_view_sensitive_fields || false

  // Calculate summary metrics from invoices
  const overdueInvoices = invoices.filter((inv) => (inv.days_past_due ?? 0) > 0)
  const overdueBalance = overdueInvoices.reduce((sum, inv) => sum + parseFloat(inv.open_amount), 0).toString()
  const oldestOverdueDays = Math.max(...overdueInvoices.map((inv) => inv.days_past_due ?? 0), 0)

  return (
    <div className="p-8 pb-12">
      <p className="text-[#56616B] mb-2 text-sm">
        <Link to="/queue" className="text-[#8A3A12] font-semibold underline">
          Work queue
        </Link>{' '}
        / {profile?.customer_name || 'Customer'}
      </p>
      <div className="flex justify-between items-end mb-5">
        <div>
          <h1 className="text-3xl leading-tight font-bold text-[#14283A] font-serif m-0">
            {profile?.customer_name || 'Customer'}
          </h1>
          <p className="text-[#56616B] mt-1">
            Customer {profile?.sap_customer_ref} &middot; Account {accounts?.sap_account_ref} &middot; Region{' '}
            {profile?.regional_business_unit} &middot; Reference data synchronized from SAP{' '}
            {data.data_freshness ? new Date(data.data_freshness).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }) : ''} UTC
          </p>
        </div>
        <button
          className="inline-block min-h-11 py-2.5 px-4 rounded font-bold border-2 border-[#14283A] bg-[#14283A] text-white"
          onClick={() => navigate(`/promise/new?customerId=${customerId}&accountId=${accounts?.customer_account_id}`)}
        >
          Record promise to pay
        </button>
      </div>

      <div className="flex gap-6 items-start">
        <div className="flex-[1.2]">
          <SectionCard title="Account summary" status={data.accounts.status}>
            {accounts && (
              <AccountSummary
                account={accounts}
                overdueBalance={overdueBalance}
                oldestOverdueDays={oldestOverdueDays}
                paymentTerms="Net 45"
                creditLimit={profile?.credit_status_indicator || null}
                queueState="Ready for action"
                isSensitiveUser={isSensitiveUser}
              />
            )}
          </SectionCard>

          <SectionCard title="Overdue invoices" status={data.invoices.status} reason={data.invoices.reason}>
            <InvoiceTable invoices={overdueInvoices} />
          </SectionCard>

          <SectionCard title="Ageing and unapplied cash" status={data.unapplied_cash?.status || 'unavailable'} reason={data.unapplied_cash?.reason || 'The SAP receivables service did not respond in time, so ageing buckets and unapplied cash cannot be shown. Other sections on this page are not affected.'}>
            <p>Ageing buckets and unapplied cash data.</p>
          </SectionCard>
        </div>

        <div className="flex-1">
          <SectionCard title="Promises to pay" status={data.promises.status}>
            <ul className="list-none m-0 p-0">
              {promises.length === 0 ? (
                <li className="py-2.5 border-b border-[#E4DECF] last:border-b-0">
                  <strong>None open.</strong>
                  <div className="text-[#47525C] text-sm">Last promise: USD 55,000.00 kept, closed 10 Dec 2024.</div>
                </li>
              ) : (
                promises.map((promise) => (
                  <li key={promise.promise_id} className="py-2.5 border-b border-[#E4DECF] last:border-b-0">
                    <strong>
                      {promise.currency_code} {parseFloat(promise.promised_amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </strong>
                    <div className="text-[#47525C] text-sm">
                      Due {new Date(promise.promised_date).toLocaleDateString('en-GB')} &middot; Status: {promise.promise_status}
                    </div>
                  </li>
                ))
              )}
            </ul>
            <div className="mt-3">
              <button
                className="inline-block min-h-11 py-2.5 px-4 rounded font-bold border-2 border-[#14283A] bg-white text-[#14283A]"
                onClick={() => navigate(`/promise/new?customerId=${customerId}&accountId=${accounts?.customer_account_id}`)}
              >
                Record promise to pay
              </button>
            </div>
          </SectionCard>

          <SectionCard title="Source interactions on file" status={data.source_interactions.status}>
            <ul className="list-none m-0 p-0">
              {interactions.length === 0 ? (
                <li className="py-2.5">No interactions recorded.</li>
              ) : (
                interactions.slice(0, 3).map((int) => (
                  <li key={int.interaction_id} className="py-2.5 border-b border-[#E4DECF] last:border-b-0">
                    <strong>
                      {int.interaction_type.charAt(0).toUpperCase() + int.interaction_type.slice(1)},{' '}
                      {new Date(int.occurred_at).toLocaleDateString('en-GB', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric',
                      })}
                    </strong>
                    <div className="text-[#47525C] text-sm">
                      {int.summary_text}. Reference {int.interaction_id}.
                    </div>
                  </li>
                ))
              )}
            </ul>
          </SectionCard>

          <SectionCard title="Dispute status" status="available">
            <p>No open dispute indicator in SAP for this customer.</p>
          </SectionCard>
        </div>
      </div>
    </div>
  )
}
