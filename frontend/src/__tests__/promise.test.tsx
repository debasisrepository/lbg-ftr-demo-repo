import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { FailedConditionList } from '../components/promise/FailedConditionList'
import { PolicyCheckPanel } from '../components/promise/PolicyCheckPanel'
import { AccountContextCard } from '../components/promise/AccountContextCard'

describe('Promise Components', () => {
  it('renders FailedConditionList with multiple conditions', () => {
    const policyFailure = {
      evaluation_result: 'deny' as const,
      failed_conditions: [
        {
          rule_code: 'PROMISE_SOURCE_REQUIRED',
          condition_type: 'field_present',
          failure_message: 'Source interaction is required.',
          parameters: {},
        },
        {
          rule_code: 'PROMISE_AMOUNT_WITHIN_SCOPE',
          condition_type: 'decimal_less_than',
          failure_message: 'Amount exceeds scope total.',
          parameters: {},
        },
      ],
    }

    render(<FailedConditionList policyFailure={policyFailure} />)

    expect(screen.getByText(/Policy check failed on 2 conditions/)).toBeTruthy()
    expect(screen.getByText('Source interaction is required.')).toBeTruthy()
    expect(screen.getByText('Amount exceeds scope total.')).toBeTruthy()
  })

  it('renders PolicyCheckPanel with no failures', () => {
    render(<PolicyCheckPanel policyFailure={null} ruleSetVersion="2025.03" />)

    expect(screen.getByText('Policy checks on save')).toBeTruthy()
    expect(screen.getByText(/Rule set version 2025.03/)).toBeTruthy()
    expect(screen.getAllByText('Passed')).toHaveLength(4)
  })

  it('renders PolicyCheckPanel with failures', () => {
    const policyFailure = {
      evaluation_result: 'deny' as const,
      failed_conditions: [
        {
          rule_code: 'PROMISE_SOURCE_REQUIRED',
          condition_type: 'field_present',
          failure_message: 'Source interaction is required.',
          parameters: {},
        },
      ],
    }

    render(<PolicyCheckPanel policyFailure={policyFailure} ruleSetVersion="2025.03" />)

    const failedElements = screen.getAllByText('Failed')
    expect(failedElements.length).toBe(1)
    const passedElements = screen.getAllByText('Passed')
    expect(passedElements.length).toBe(3)
  })

  it('renders AccountContextCard with all fields', () => {
    render(
      <AccountContextCard
        overdueBalance="50000.00"
        currencyCode="USD"
        oldestOverdueDays={62}
        queueState="Ready for action"
        openPromisesCount={0}
      />
    )

    expect(screen.getByText('Account context')).toBeTruthy()
    expect(screen.getByText(/50,000\.00/)).toBeTruthy()
    expect(screen.getByText('62 days')).toBeTruthy()
    expect(screen.getByText('Ready for action')).toBeTruthy()
    expect(screen.getByText('None')).toBeTruthy()
  })

  it('renders AccountContextCard with open promises', () => {
    render(
      <AccountContextCard
        overdueBalance="50000.00"
        currencyCode="USD"
        oldestOverdueDays={62}
        queueState="Ready for action"
        openPromisesCount={2}
      />
    )

    expect(screen.getByText('2')).toBeTruthy()
  })
})
