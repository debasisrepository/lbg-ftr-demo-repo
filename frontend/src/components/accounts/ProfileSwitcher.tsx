import { useState } from 'react'
import { ProfileInfo } from '../../features/accounts/useProfiles'

interface ProfileSwitcherProps {
  profiles: ProfileInfo[]
  activeProfileId: string | null
  onProfileChange: (profileId: string) => Promise<void>
}

export function ProfileSwitcher({ profiles, activeProfileId, onProfileChange }: ProfileSwitcherProps) {
  const [switching, setSwitching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (profiles.length <= 1) {
    return null
  }

  const handleProfileChange = async (profileId: string) => {
    if (switching || profileId === activeProfileId) return
    
    setSwitching(true)
    setError(null)
    
    try {
      await onProfileChange(profileId)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to switch profile')
    } finally {
      setSwitching(false)
    }
  }

  return (
    <div>
      <div role="tablist" aria-label="Profile" style={{ display: 'flex', border: '1px solid #8d8d8d', position: 'relative' }}>
        {profiles.map((profile) => {
          const isActive = profile.profile_id === activeProfileId
          return (
            <button
              key={profile.profile_id}
              role="tab"
              aria-selected={isActive}
              aria-busy={switching}
              disabled={switching}
              onClick={() => handleProfileChange(profile.profile_id)}
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
                cursor: switching ? 'wait' : 'pointer',
                fontFamily: 'inherit',
                opacity: switching ? 0.6 : 1,
              }}
            >
              {profile.display_name}
              {isActive && (
                <span style={{ position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clip: 'rect(0,0,0,0)' }}>
                  (active)
                </span>
              )}
            </button>
          )
        })}
      </div>
      {error && (
        <div role="alert" style={{ marginTop: '8px', padding: '12px', background: '#fef2f2', border: '1px solid #dc2626', color: '#991b1b', fontSize: '14px' }}>
          {error}
        </div>
      )}
    </div>
  )
}
