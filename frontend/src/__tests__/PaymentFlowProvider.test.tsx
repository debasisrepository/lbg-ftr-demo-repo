import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { PaymentFlowProvider, usePaymentFlow } from '../features/payments/PaymentFlowProvider'

function TestComponent() {
  const { state, preparedPayment, setPreparedPayment, transitionTo, resetFlow } =
    usePaymentFlow()

  return (
    <div>
      <div data-testid="state">{state}</div>
      <div data-testid="payment-order-id">
        {preparedPayment?.payment_order_id || 'none'}
      </div>
      <button
        onClick={() =>
          setPreparedPayment({
            payment_order_id: 'test-123',
            customer_payment_ref: 'PAY001',
            payment_reference: 'Test',
            amount_minor: 5000,
            currency_code: 'GBP',
            source_account_name: 'Current',
            payee_name: 'Payee',
            limit_checks_passed: true,
            risk_decision: 'allow',
            requires_approval: true,
            dynamic_link_digest: 'abc',
          })
        }
      >
        Set Payment
      </button>
      <button onClick={() => transitionTo('approving')}>Transition</button>
      <button onClick={resetFlow}>Reset</button>
    </div>
  )
}

describe('PaymentFlowProvider', () => {
  it('provides initial state', () => {
    render(
      <PaymentFlowProvider>
        <TestComponent />
      </PaymentFlowProvider>
    )

    expect(screen.getByTestId('state')).toHaveTextContent('entering')
    expect(screen.getByTestId('payment-order-id')).toHaveTextContent('none')
  })

  it('sets prepared payment and transitions to prepared', async () => {
    const user = userEvent.setup()
    render(
      <PaymentFlowProvider>
        <TestComponent />
      </PaymentFlowProvider>
    )

    await user.click(screen.getByText('Set Payment'))

    expect(screen.getByTestId('state')).toHaveTextContent('prepared')
    expect(screen.getByTestId('payment-order-id')).toHaveTextContent('test-123')
  })

  it('transitions between states', async () => {
    const user = userEvent.setup()
    render(
      <PaymentFlowProvider>
        <TestComponent />
      </PaymentFlowProvider>
    )

    await user.click(screen.getByText('Transition'))

    expect(screen.getByTestId('state')).toHaveTextContent('approving')
  })

  it('resets flow to initial state', async () => {
    const user = userEvent.setup()
    render(
      <PaymentFlowProvider>
        <TestComponent />
      </PaymentFlowProvider>
    )

    await user.click(screen.getByText('Set Payment'))
    expect(screen.getByTestId('state')).toHaveTextContent('prepared')

    await user.click(screen.getByText('Reset'))

    expect(screen.getByTestId('state')).toHaveTextContent('entering')
    expect(screen.getByTestId('payment-order-id')).toHaveTextContent('none')
  })
})
