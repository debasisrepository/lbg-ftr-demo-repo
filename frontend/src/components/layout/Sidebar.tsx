import { NavLink } from 'react-router-dom'

const navItems = [
  { path: '/', label: 'Home', icon: '🏠' },
  { path: '/queue', label: 'Work Queue', icon: '📋' },
  { path: '/customer/00000000-0000-0000-0000-000000000001', label: 'Customer 360', icon: '👤' },
]

export function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-border min-h-[calc(100vh-4rem)]">
      <nav className="p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary text-white'
                      : 'text-text-primary hover:bg-surface'
                  }`
                }
              >
                <span className="text-xl">{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  )
}
