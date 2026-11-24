import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SectionCard } from '../components/customer/SectionCard'
import { AccountSummary } from '../components/customer/AccountSummary'
import { InvoiceTable } from '../components/customer/InvoiceTable'

describe('Customer360 Components', () => {
  it('renders SectionCard with available status', () => {
    render(
      <SectionCard title="Test Section" status="available">
        <p>Content</p>
      </SectionCard>
    )
    expect(screen.getByText('Test Section')).toBeTruthy()
    expect(screen.getByText('Available')).toBeTruthy()
    expect(screen.getByText('Content')).toBeTruthy()
  })

  it('renders SectionCard with unavailable status and reason', () => {
    render(
      <SectionCard title="Test Section" status="unavailable" reason="Service timeout">
        <p>Content</p>
      </SectionCard>
    )
    expect(screen.getByText('Test Section')).toBeTruthy()
    expect(screen.getByText('Unavailable')).toBeTruthy()
    expect(screen.getByText(/Service timeout/)).toBeTruthy()
  })

  it('renders AccountSummary with all fields', () => {
    const account = {
      customer_account_id: '1',
      sap_account_ref: 'ACCT001',
      company_code: '1000',
      currency_code: 'USD',
      account_status: 'active',
      risk_segment: 'medium',
      portfolio_ref: 'PORT001',
      collector_owner_user_id: null,
      open_balance: '50000.00',
    }

    render(
      <AccountSummary
        account={account}
        overdueBalance="20000.00"
        oldestOverdueDays={45}
        paymentTerms="Net 30"
        creditLimit="100000.00"
        queueState="Ready"
        isSensitiveUser={true}
      />
    )

    expect(screen.getByText('Total open balance')).toBeTruthy()
    expect(screen.getByText(/50,000\.00/)).toBeTruthy()
    expect(screen.getByText('45 days')).toBeTruthy()
    expect(screen.getByText('Net 30')).toBeTruthy()
  })

  it('masks credit limit for non-sensitive users', () => {
    const account = {
      customer_account_id: '1',
      sap_account_ref: 'ACCT001',
      company_code: '1000',
      currency_code: 'USD',
      account_status: 'active',
      risk_segment: 'medium',
      portfolio_ref: 'PORT001',
      collector_owner_user_id: null,
      open_balance: '50000.00',
    }

    render(
      <AccountSummary
        account={account}
        overdueBalance="20000.00"
        oldestOverdueDays={45}
        paymentTerms="Net 30"
        creditLimit="100000.00"
        queueState="Ready"
        isSensitiveUser={false}
      />
    )

    expect(screen.getByText(/Masked for your role/)).toBeTruthy()
  })

  it('renders InvoiceTable with invoices', () => {
    const invoices = [
      {
        invoice_id: '1',
        sap_invoice_ref: 'INV001',
        invoice_number: '9000001',
        document_date: '2025-01-01',
        due_date: '2025-02-01',
        invoice_amount: '1000.00',
        open_amount: '1000.00',
        currency_code: 'USD',
        invoice_status: 'open',
        days_past_due: 30,
      },
    ]

    render(<InvoiceTable invoices={invoices} />)

    expect(screen.getByText('9000001')).toBeTruthy()
    expect(screen.getByText('1,000.00')).toBeTruthy()
    expect(screen.getByText('30')).toBeTruthy()
  })

  it('renders InvoiceTable empty state', () => {
    render(<InvoiceTable invoices={[]} />)
    expect(screen.getByText('No overdue invoices.')).toBeTruthy()
  })
})
