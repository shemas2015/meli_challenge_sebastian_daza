import { useState } from 'react'
import './App.css'
import Sidebar from './components/Sidebar.jsx'
import TopBar from './components/TopBar.jsx'
import ReportsList from './components/ReportsList.jsx'
import NewReportModal from './components/NewReportModal.jsx'

function App() {
  const [showNewReport, setShowNewReport] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0)

  const handleSuccess = () => {
    setShowNewReport(false)
    setRefreshKey((k) => k + 1)
  }

  return (
    <div className="app-layout">
      <Sidebar />
      <div className="app-main">
        <TopBar onNewReport={() => setShowNewReport(true)} />
        <div className="app-content">
          <ReportsList refreshKey={refreshKey} />
        </div>
      </div>
      {showNewReport && (
        <NewReportModal
          onClose={() => setShowNewReport(false)}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  )
}

export default App
