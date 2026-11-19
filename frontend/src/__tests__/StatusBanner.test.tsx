import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBanner } from '../components/accounts/StatusBanner'

describe('StatusBanner', () => {
  it('should render info banner', () => {
    render(<StatusBanner message="Test info message" type="info" />)

    expect(screen.getByText('Test info message')).toBeInTheDocument()
  })

  it('should render warning banner', () => {
    render(<StatusBanner message="Test warning message" type="warning" />)

    expect(screen.getByText('Test warning message')).toBeInTheDocument()
  })

  it('should default to info type', () => {
    render(<StatusBanner message="Default message" />)

    expect(screen.getByText('Default message')).toBeInTheDocument()
  })
})
