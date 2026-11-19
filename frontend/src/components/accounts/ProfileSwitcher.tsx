import { ProfileInfo } from '../../features/accounts/useProfiles'

interface ProfileSwitcherProps {
  profiles: ProfileInfo[]
  activeProfileId: string | null
  onProfileChange: (profileId: string) => void
}

export function ProfileSwitcher({ profiles, activeProfileId, onProfileChange }: ProfileSwitcherProps) {
  if (profiles.length <= 1) {
    return null
  }

  return (
    <div role="tablist" aria-label="Profile" style={{ display: 'flex', border: '1px solid #8d8d8d' }}>
      {profiles.map((profile) => {
        const isActive = profile.profile_id === activeProfileId
        return (
          <button
            key={profile.profile_id}
            role="tab"
            aria-selected={isActive}
            onClick={() => onProfileChange(profile.profile_id)}
            style={{
              flex: 1,
              textAlign: 'center',
              minHeight: '44px',
              lineHeight: '44px',
              fontSize: '14px',
              fontWeight: 600,
              background: isActive ? '#161616' : 'transparent',
              color: isActive ? '#fff' : '#161616',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            {profile.display_name}
          </button>
        )
      })}
    </div>
  )
}
