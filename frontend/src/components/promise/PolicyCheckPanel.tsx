import { PolicyFailureDetail } from '../../types/promise'

interface PolicyCheckPanelProps {
  policyFailure: PolicyFailureDetail | null
  ruleSetVersion: string
}

interface PolicyRule {
  code: string
  label: string
}

const POLICY_RULES: PolicyRule[] = [
  { code: 'PROMISE_SOURCE_REQUIRED', label: 'Source interaction present' },
  { code: 'PROMISE_AMOUNT_WITHIN_SCOPE', label: 'Promised amount within selected scope total' },
  { code: 'PROMISE_DATE_VALID', label: 'Promised date is today or later' },
  { code: 'PROMISE_SCOPE_BELONGS_TO_ACCOUNT', label: 'Scope invoices belong to this customer account' },
]

export function PolicyCheckPanel({ policyFailure, ruleSetVersion }: PolicyCheckPanelProps) {
  const failedCodes = new Set(policyFailure?.failed_conditions.map((c) => c.rule_code) || [])

  return (
    <section className="bg-white border border-[#D5CDBB] rounded-md p-5 mb-6" aria-labelledby="rules-title">
      <h2 id="rules-title" className="text-lg font-bold text-[#14283A] font-serif mb-4">
        Policy checks on save
      </h2>
      <p className="text-xs text-[#47525C] mb-2">
        Rule set version {ruleSetVersion} &middot; evaluated by the server on every save.
      </p>
      <ul className="list-none m-0 p-0">
        {POLICY_RULES.map((rule) => {
          const failed = failedCodes.has(rule.code)
          return (
            <li
              key={rule.code}
              className="py-2 border-b border-[#E4DECF] flex gap-2.5 items-baseline last:border-b-0"
            >
              <span className={`min-w-16 font-bold ${failed ? 'text-[#8E1F13]' : 'text-[#0F5B46]'}`}>
                {failed ? 'Failed' : 'Passed'}
              </span>
              <span>{rule.label}</span>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
