interface RoleSwitcherProps {
  activeRoleCode: string
  activeRoleLabel: string
  availableRoles: Array<{ role_code: string; role_label: string }>
  onRoleChange: (roleCode: string) => void
  disabled?: boolean
}

export function RoleSwitcher({
  activeRoleCode,
  availableRoles,
  onRoleChange,
  disabled,
}: RoleSwitcherProps) {
  return (
    <div className="flex items-center gap-3">
      <label htmlFor="role-select" className="font-semibold text-sm">
        Active role view
      </label>
      <select
        id="role-select"
        name="role-select"
        className="min-w-[260px] min-h-[44px] px-4 py-2 bg-white border border-[#7A858F] rounded"
        value={activeRoleCode}
        onChange={(e) => onRoleChange(e.target.value)}
        disabled={disabled}
      >
        {availableRoles.map((role) => (
          <option key={role.role_code} value={role.role_code}>
            {role.role_label}
          </option>
        ))}
      </select>
    </div>
  )
}
