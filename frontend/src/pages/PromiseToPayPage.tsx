import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { useCustomerView } from '../hooks/useCustomerView'
import { PromiseForm } from '../components/promise/PromiseForm'
import { PolicyCheckPanel } from '../components/promise/PolicyCheckPanel'
import { AccountContextCard } from '../components/promise/AccountContextCard'
import { usePromises } from '../hooks/usePromises'

export function PromiseToPayPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const customerId = searchParams.get('customerId')
  const accountId = searchParams.get('accountId')
  
  const { data, loading, error } = useCustomerView(customerId || undefined)
  const { policyFailure } = usePromises()

  if (loading) {
    return (
      <div className="p-8">
        <div className="text-[#47525C]">Loading customer data...</div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="p-8">
        <div className="text-[#8E1F13]">Error: {error || 'Customer not found'}</div>
      </div>
    )
  }

  const profile = data.profile.data
  const accounts = data.accounts.data?.[0]
  const invoices = data.invoices.data || []
  const interactions = data.source_interactions.data || []
  const promises = data.promises.data || []

  if (!accountId || !accounts) {
    return (
      <div className="p-8">
        <div className="text-[#8E1F13]">No customer account specified.</div>
      </div>
    )
  }

  // Calculate metrics
  const overdueInvoices = invoices.filter((inv) => (inv.days_past_due ?? 0) > 0)
  const overdueBalance = overdueInvoices.reduce((sum, inv) => sum + parseFloat(inv.open_amount), 0).toString()
  const oldestOverdueDays = Math.max(...overdueInvoices.map((inv) => inv.days_past_due ?? 0), 0)
  const openPromisesCount = promises.filter((p) => p.promise_status === 'active').length

  const handleSuccess = () => {
    navigate(`/customer/${customerId}`)
  }

  const handleCancel = () => {
    navigate(`/customer/${customerId}`)
  }

  return (
    <div className="p-8 pb-12">
      <p className="text-[#56616B] mb-2 text-sm">
        <Link to={`/customer/${customerId}`} className="text-[#8A3A12] font-semibold underline">
          Customer 360
        </Link>{' '}
        / {profile?.customer_name || 'Customer'} / Record promise to pay
      </p>
      <div className="mb-5">
        <h1 className="text-3xl leading-tight font-bold text-[#14283A] font-serif m-0">Record promise to pay</h1>
        <p className="text-[#56616B] mt-1">
          {profile?.customer_name} &middot; Customer {profile?.sap_customer_ref} &middot; Amount, date, scope and
          source interaction are all required.
        </p>
      </div>

      <div className="flex gap-6 items-start">
        <div className="flex-[1.4]">
          <PromiseForm
            customerId={customerId || ''}
            customerAccountId={accountId}
            customerName={profile?.customer_name || ''}
            invoices={overdueInvoices}
            interactions={interactions}
            onSuccess={handleSuccess}
            onCancel={handleCancel}
          />
        </div>

        <div className="flex-1">
          <AccountContextCard
            overdueBalance={overdueBalance}
            currencyCode={accounts.currency_code}
            oldestOverdueDays={oldestOverdueDays}
            queueState="Ready for action"
            openPromisesCount={openPromisesCount}
          />

          <PolicyCheckPanel policyFailure={policyFailure} ruleSetVersion="2025.03" />

          <div className="p-3 border border-dashed border-[#7A858F] rounded text-[#47525C] text-sm bg-[#FBF9F4]">
            <strong>Design note (FR-PTP-001, FR-DTC-001).</strong> The form never decides on its own whether a promise
            is allowed. It shows the failed conditions returned by the server. A retry with the same idempotency key
            does not create a second promise. Follow-up scheduling, payment plans and breach handling are deferred.
          </div>
        </div>
      </div>
    </div>
  )
}
