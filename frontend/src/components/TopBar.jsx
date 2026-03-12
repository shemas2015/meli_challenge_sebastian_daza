import { useState } from 'react'
import './TopBar.css'

const SearchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
  </svg>
)

const BellIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
  </svg>
)

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z" />
  </svg>
)

function TopBar({ onNewReport }) {
  const [searchValue, setSearchValue] = useState('')
  const [hasNotification] = useState(true)

  return (
    <header className="topbar">
      <div className="topbar-search">
        <span className="topbar-search-icon">
          <SearchIcon />
        </span>
        <input
          type="text"
          className="topbar-search-input"
          placeholder="Search reports..."
          value={searchValue}
          onChange={(e) => setSearchValue(e.target.value)}
        />
      </div>

      <div className="topbar-actions">
        <button className="topbar-bell" aria-label="Notifications">
          <BellIcon />
          {hasNotification && <span className="topbar-bell-badge" />}
        </button>

        <button className="topbar-btn-generate" onClick={onNewReport}>
          <PlusIcon />
          <span>Generate New Report</span>
        </button>
      </div>
    </header>
  )
}

export default TopBar
