import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueueFilters } from '../components/queue/QueueFilters'
import userEvent from '@testing-library/user-event'

describe('QueueFilters', () => {
  it('renders filter controls', () => {
    const onFilterChange = vi.fn()
    render(<QueueFilters onFilterChange={onFilterChange} />)

    expect(screen.getByLabelText(/Show/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Customer/i)).toBeInTheDocument()
  })

  it('calls onFilterChange when show filter changes', async () => {
    const onFilterChange = vi.fn()
    const user = userEvent.setup()
    
    render(<QueueFilters onFilterChange={onFilterChange} />)

    const showSelect = screen.getByLabelText(/Show/i)
    await user.selectOptions(showSelect, 'standard')

    expect(onFilterChange).toHaveBeenCalledWith({
      showNonStandard: 'standard',
      customerSearch: '',
    })
  })

  it('calls onFilterChange when customer search changes', async () => {
    const onFilterChange = vi.fn()
    const user = userEvent.setup()
    
    render(<QueueFilters onFilterChange={onFilterChange} />)

    const searchInput = screen.getByLabelText(/Customer/i)
    await user.type(searchInput, 'ABC')

    // Check the last call after typing
    expect(onFilterChange).toHaveBeenLastCalledWith({
      showNonStandard: 'all',
      customerSearch: 'ABC',
    })
  })
})
