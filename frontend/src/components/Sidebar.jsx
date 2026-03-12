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
    id: 'dashboard',
    label: 'Dashboard',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
      </svg>
    ),
  },
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
  {
    id: 'scans',
    label: 'Scans',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
      </svg>
    ),
  },
  {
    id: 'assets',
    label: 'Assets',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M20 6h-2.18c.07-.44.18-.88.18-1.35C18 2.53 15.5 1 13.5 1c-1.35 0-2.37.48-3.1 1.15L9 4H5C3.35 4 2 5.35 2 7v11c0 1.65 1.35 3 3 3h14c1.65 0 3-1.35 3-3V9c0-1.65-1.35-3-3-3zm-8.93 2.07L12 7.16l1.5-1.58C13.96 5.21 14.67 5 15.5 5c1.1 0 1.5.65 1.5 1.65 0 .57-.23 1.1-.5 1.35H10.5l1.57-1.93zM20 18H4V7h4l-2.5 2.5H20v8.5z" />
      </svg>
    ),
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z" />
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
