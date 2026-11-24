import { PolicyFailureDetail } from '../../types/promise'

interface FailedConditionListProps {
  policyFailure: PolicyFailureDetail
}

export function FailedConditionList({ policyFailure }: FailedConditionListProps) {
  return (
    <div className="p-3.5 border-2 border-[#A4281A] bg-[#FBE9E6] rounded mb-5 text-[#5A1710]" role="alert">
      <strong>This promise was not saved. Policy check failed on {policyFailure.failed_conditions.length} condition{policyFailure.failed_conditions.length !== 1 ? 's' : ''}:</strong>
      <ul className="mt-2 ml-5 pl-0">
        {policyFailure.failed_conditions.map((condition, index) => (
          <li key={index}>{condition.failure_message}</li>
        ))}
      </ul>
    </div>
  )
}
