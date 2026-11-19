/**
 * Payment Flow Provider
 * Manages client-side payment flow state machine
 * States: entering → prepared → approving → friction → submitting → outcome
 */

import React, { createContext, useContext, useState, ReactNode } from 'react'
import { PreparedPayment } from './usePreparePayment'

type PaymentFlowState =
  | 'entering'
  | 'prepared'
  | 'approving'
  | 'friction'
  | 'submitting'
  | 'outcome'

export interface RiskFriction {
  type: 'warn' | 'challenge' | 'hold' | 'block'
  title: string
  message: string
  requiresPurpose?: boolean
}

interface PaymentFlowContextValue {
  state: PaymentFlowState
  preparedPayment: PreparedPayment | null
  riskFriction: RiskFriction | null
  paymentOrderId: string | null
  
  setPreparedPayment: (payment: PreparedPayment) => void
  setRiskFriction: (friction: RiskFriction | null) => void
  setPaymentOrderId: (id: string) => void
  transitionTo: (state: PaymentFlowState) => void
  resetFlow: () => void
}

const PaymentFlowContext = createContext<PaymentFlowContextValue | undefined>(
  undefined
)

export function PaymentFlowProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<PaymentFlowState>('entering')
  const [preparedPayment, setPreparedPaymentState] =
    useState<PreparedPayment | null>(null)
  const [riskFriction, setRiskFrictionState] = useState<RiskFriction | null>(
    null
  )
  const [paymentOrderId, setPaymentOrderIdState] = useState<string | null>(
    null
  )

  const setPreparedPayment = (payment: PreparedPayment) => {
    setPreparedPaymentState(payment)
    setPaymentOrderIdState(payment.payment_order_id)
    setState('prepared')
  }

  const setRiskFriction = (friction: RiskFriction | null) => {
    setRiskFrictionState(friction)
    if (friction) {
      setState('friction')
    }
  }

  const setPaymentOrderId = (id: string) => {
    setPaymentOrderIdState(id)
  }

  const transitionTo = (newState: PaymentFlowState) => {
    setState(newState)
  }

  const resetFlow = () => {
    setState('entering')
    setPreparedPaymentState(null)
    setRiskFrictionState(null)
    setPaymentOrderIdState(null)
  }

  return (
    <PaymentFlowContext.Provider
      value={{
        state,
        preparedPayment,
        riskFriction,
        paymentOrderId,
        setPreparedPayment,
        setRiskFriction,
        setPaymentOrderId,
        transitionTo,
        resetFlow,
      }}
    >
      {children}
    </PaymentFlowContext.Provider>
  )
}

export function usePaymentFlow() {
  const context = useContext(PaymentFlowContext)
  if (!context) {
    throw new Error('usePaymentFlow must be used within PaymentFlowProvider')
  }
  return context
}
