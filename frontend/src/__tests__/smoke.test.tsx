import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { Header } from '../components/layout/Header'
import { Sidebar } from '../components/layout/Sidebar'
import { AuthProvider } from '../lib/auth-context'
import { formatCurrency, formatDate } from '../lib/format'

describe('Smoke Tests', () => {
  it('renders Header component', () => {
    render(
      <BrowserRouter>
        <AuthProvider>
          <Header />
        </AuthProvider>
      </BrowserRouter>
    )
    expect(screen.getByText('Receivables & Collections')).toBeInTheDocument()
  })

  it('renders Sidebar component with navigation', () => {
    render(
      <BrowserRouter>
        <Sidebar />
      </BrowserRouter>
    )
    expect(screen.getByText('Home')).toBeInTheDocument()
    expect(screen.getByText('Work Queue')).toBeInTheDocument()
  })

  it('formats currency correctly', () => {
    expect(formatCurrency(1234.56)).toBe('$1,234.56')
    expect(formatCurrency(0)).toBe('$0.00')
  })

  it('formats dates correctly', () => {
    const result = formatDate('2024-01-15T10:30:00Z')
    expect(result).toMatch(/Jan/)
    expect(result).toMatch(/15/)
    expect(result).toMatch(/2024/)
  })
})
