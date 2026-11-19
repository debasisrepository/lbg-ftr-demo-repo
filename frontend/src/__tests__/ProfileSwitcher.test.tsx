import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ProfileSwitcher } from '../components/accounts/ProfileSwitcher'
import { ProfileInfo } from '../features/accounts/useProfiles'

describe('ProfileSwitcher', () => {
  const mockProfiles: ProfileInfo[] = [
    {
      profile_id: 'profile-1',
      customer_id: 'cust-1',
      profile_type: 'personal',
      display_name: 'Personal',
      status: 'active',
      entitlements: [],
    },
    {
      profile_id: 'profile-2',
      customer_id: 'cust-1',
      profile_type: 'business',
      display_name: 'Business',
      status: 'active',
      entitlements: [],
    },
  ]

  it('should not render when only one profile', () => {
    const { container } = render(
      <ProfileSwitcher
        profiles={[mockProfiles[0]]}
        activeProfileId="profile-1"
        onProfileChange={vi.fn()}
      />
    )

    expect(container.firstChild).toBeNull()
  })

  it('should render profile tabs', () => {
    render(
      <ProfileSwitcher
        profiles={mockProfiles}
        activeProfileId="profile-1"
        onProfileChange={vi.fn()}
      />
    )

    expect(screen.getByRole('tab', { name: 'Personal' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Business' })).toBeInTheDocument()
  })

  it('should mark active profile', () => {
    render(
      <ProfileSwitcher
        profiles={mockProfiles}
        activeProfileId="profile-1"
        onProfileChange={vi.fn()}
      />
    )

    const personalTab = screen.getByRole('tab', { name: 'Personal' })
    const businessTab = screen.getByRole('tab', { name: 'Business' })

    expect(personalTab).toHaveAttribute('aria-selected', 'true')
    expect(businessTab).toHaveAttribute('aria-selected', 'false')
  })

  it('should call onProfileChange when clicking tab', async () => {
    const user = userEvent.setup()
    const handleChange = vi.fn()

    render(
      <ProfileSwitcher
        profiles={mockProfiles}
        activeProfileId="profile-1"
        onProfileChange={handleChange}
      />
    )

    const businessTab = screen.getByRole('tab', { name: 'Business' })
    await user.click(businessTab)

    expect(handleChange).toHaveBeenCalledWith('profile-2')
  })
})
