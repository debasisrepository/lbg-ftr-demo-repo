import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { RiskFrictionPanel } from '../components/payments/RiskFrictionPanel'

describe('RiskFrictionPanel', () => {
  it('renders warning message', () => {
    render(
      <RiskFrictionPanel
        type="warn"
        title="Warning title"
        message="Warning message"
      />
    )

    expect(screen.getByText(/Warning title/i)).toBeInTheDocument()
    expect(screen.getByText(/Warning message/i)).toBeInTheDocument()
  })

  it('shows acknowledgement button for warn type', () => {
    render(
      <RiskFrictionPanel
        type="warn"
        title="Warning"
        message="Message"
        onAcknowledge={vi.fn()}
      />
    )

    expect(
      screen.getByRole('button', { name: /I've checked, continue to approve/i })
    ).toBeInTheDocument()
  })

  it('shows cancel button for warn type', () => {
    render(
      <RiskFrictionPanel
        type="warn"
        title="Warning"
        message="Message"
        onCancel={vi.fn()}
      />
    )

    expect(
      screen.getByRole('button', { name: /Stop this payment/i })
    ).toBeInTheDocument()
  })

  it('shows purpose options for challenge type', () => {
    render(
      <RiskFrictionPanel
        type="challenge"
        title="Challenge"
        message="Message"
        requiresPurpose={true}
      />
    )

    expect(screen.getByText(/What is this payment for/i)).toBeInTheDocument()
    expect(screen.getByText(/Personal expense/i)).toBeInTheDocument()
    expect(screen.getByText(/Business payment/i)).toBeInTheDocument()
  })

  it('disables continue button when purpose not selected', () => {
    render(
      <RiskFrictionPanel
        type="challenge"
        title="Challenge"
        message="Message"
        requiresPurpose={true}
        onProvidePurpose={vi.fn()}
      />
    )

    const continueButton = screen.getByRole('button', { name: /Continue/i })
    expect(continueButton).toBeDisabled()
  })

  it('enables continue button when purpose selected', async () => {
    const user = userEvent.setup()
    render(
      <RiskFrictionPanel
        type="challenge"
        title="Challenge"
        message="Message"
        requiresPurpose={true}
        onProvidePurpose={vi.fn()}
      />
    )

    const radio = screen.getByLabelText(/Personal expense/i)
    await user.click(radio)

    const continueButton = screen.getByRole('button', { name: /Continue/i })
    expect(continueButton).not.toBeDisabled()
  })

  it('shows next steps for hold type', () => {
    render(
      <RiskFrictionPanel type="hold" title="Held" message="Message" />
    )

    expect(screen.getByText(/Next steps:/i)).toBeInTheDocument()
    expect(
      screen.getByText(/We're reviewing this payment/i)
    ).toBeInTheDocument()
  })

  it('shows next steps for block type', () => {
    render(
      <RiskFrictionPanel type="block" title="Blocked" message="Message" />
    )

    expect(screen.getByText(/Next steps:/i)).toBeInTheDocument()
    expect(
      screen.getByText(/This payment cannot be sent right now/i)
    ).toBeInTheDocument()
  })
})
