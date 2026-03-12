import React from 'react'
import './Sidebar.css'

const ShieldIcon = () => (
  <svg
    width="28"
    height="28"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
  >
    <path
      d="M12 2L4 6v6c0 5.55 3.84 10.74 8 12 4.16-1.26 8-6.45 8-12V6l-8-4z"
      fill="#3b82f6"
    />
    <path
      d="M10.5 14.5l-2.5-2.5 1.06-1.06 1.44 1.44 3.44-3.44L15 10l-4.5 4.5z"
      fill="white"
    />
  </svg>
)

const navItems = [
  {
    id: 'reports',
    label: 'Reports',
    active: true,
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zM16 18H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
      </svg>
    ),
  },
]

function Sidebar() {
  return (
    <aside className="sidebar">
      {/* Logo area */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">
          <ShieldIcon />
        </div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-title">Security Platform</span>
          <span className="sidebar-logo-subtitle">Admin Dashboard</span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <ul className="sidebar-nav-list">
          {navItems.map((item) => (
            <li key={item.id}>
              <a
                href="#"
                className={`sidebar-nav-item${item.active ? ' sidebar-nav-item--active' : ''}`}
                onClick={(e) => e.preventDefault()}
              >
                <span className="sidebar-nav-icon">{item.icon}</span>
                <span className="sidebar-nav-label">{item.label}</span>
              </a>
            </li>
          ))}
        </ul>
      </nav>

      {/* User profile at bottom */}
      <div className="sidebar-user">
        <div className="sidebar-user-avatar">A</div>
        <div className="sidebar-user-info">
          <span className="sidebar-user-name">Sebastián Daza</span>
          <span className="sidebar-user-role">Chief Security Officer</span>
        </div>
      </div>
    </aside>
  )
}

export default Sidebar
