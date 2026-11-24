import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { RoleSwitcher } from '../components/workspace/RoleSwitcher'
import userEvent from '@testing-library/user-event'

describe('RoleSwitcher', () => {
  const mockRoles = [
    { role_code: 'collections_analyst', role_label: 'Collections Analyst' },
    { role_code: 'collections_reviewer', role_label: 'Collections Reviewer' },
  ]

  it('renders with active role selected', () => {
    const onRoleChange = vi.fn()
    render(
      <RoleSwitcher
        activeRoleCode="collections_analyst"
        activeRoleLabel="Collections Analyst"
        availableRoles={mockRoles}
        onRoleChange={onRoleChange}
      />
    )

    const select = screen.getByRole('combobox', { name: /active role view/i })
    expect(select).toHaveValue('collections_analyst')
  })

  it('calls onRoleChange when role is changed', async () => {
    const onRoleChange = vi.fn()
    const user = userEvent.setup()
    
    render(
      <RoleSwitcher
        activeRoleCode="collections_analyst"
        activeRoleLabel="Collections Analyst"
        availableRoles={mockRoles}
        onRoleChange={onRoleChange}
      />
    )

    const select = screen.getByRole('combobox', { name: /active role view/i })
    await user.selectOptions(select, 'collections_reviewer')

    expect(onRoleChange).toHaveBeenCalledWith('collections_reviewer')
  })

  it('renders all available roles as options', () => {
    const onRoleChange = vi.fn()
    render(
      <RoleSwitcher
        activeRoleCode="collections_analyst"
        activeRoleLabel="Collections Analyst"
        availableRoles={mockRoles}
        onRoleChange={onRoleChange}
      />
    )

    expect(screen.getByRole('option', { name: 'Collections Analyst' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Collections Reviewer' })).toBeInTheDocument()
  })
})
