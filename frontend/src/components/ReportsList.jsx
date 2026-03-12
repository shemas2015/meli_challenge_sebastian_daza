import React, { useState, useEffect } from 'react'
import './ReportsList.css'
import ReportDrawer from './ReportDrawer'

const API_URL = import.meta.env.VITE_API_URL || 'http://100.93.112.98:8000'

/* ── Helpers ── */

const parseProgress = (progressStr, processed, total) => {
  if (total === 0) return 0
  if (typeof progressStr === 'string' && progressStr.includes('/')) {
    const [p, t] = progressStr.split('/').map(Number)
    return t > 0 ? Math.round((p / t) * 100) : 0
  }
  return Math.round((processed / total) * 100)
}

const formatDate = (isoString) => {
  const d = new Date(isoString)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const isUrl = (name) => /^https?:\/\//i.test(name)

/* ── Sub-components ── */

const FileIcon = ({ fileName }) => {
  if (isUrl(fileName)) {
    return (
      <span className="file-icon file-icon--url" title="URL">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
          <path d="M3.9 12c0-1.71 1.39-3.1 3.1-3.1h4V7H7c-2.76 0-5 2.24-5 5s2.24 5 5 5h4v-1.9H7c-1.71 0-3.1-1.39-3.1-3.1zM8 13h8v-2H8v2zm9-6h-4v1.9h4c1.71 0 3.1 1.39 3.1 3.1s-1.39 3.1-3.1 3.1h-4V17h4c2.76 0 5-2.24 5-5s-2.24-5-5-5z" />
        </svg>
      </span>
    )
  }
  return (
    <span className="file-icon file-icon--doc" title="Document">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z" />
      </svg>
    </span>
  )
}

const StatusBadge = ({ status }) => {
  const cls =
    status === 'COMPLETED' ? 'badge badge--completed' :
    status === 'PENDING'   ? 'badge badge--pending' :
    status === 'PROCESSING'? 'badge badge--pending' :
    status === 'FAILED'    ? 'badge badge--failed' :
                             'badge badge--inconclusive'
  return <span className={cls}>{status}</span>
}

const ProgressBar = ({ value }) => (
  <div className="progress-cell">
    <div className="progress-track">
      <div className="progress-fill" style={{ width: `${value}%` }} />
    </div>
    <span className="progress-label">{value}% Processed</span>
  </div>
)

const ChevronLeft = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M15.41 16.59L10.83 12l4.58-4.59L14 6l-6 6 6 6z" />
  </svg>
)

const ChevronRight = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
    <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z" />
  </svg>
)

/* ── Main component ── */

const PAGE_SIZE = 10

function ReportsList({ refreshKey }) {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedReport, setSelectedReport] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  const handleViewDetails = (report) => {
    setLoadingDetail(true)
    fetch(`${API_URL}/api/vulnerabilities/uploads/${report.id}/`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setSelectedReport(data)
        setLoadingDetail(false)
      })
      .catch(() => {
        setSelectedReport(report)
        setLoadingDetail(false)
      })
  }

  useEffect(() => {
    fetch(`${API_URL}/api/vulnerabilities/uploads/`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => {
        setReports(data)
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message)
        setLoading(false)
      })
  }, [refreshKey])

  const totalPages = Math.max(1, Math.ceil(reports.length / PAGE_SIZE))
  const pageReports = reports.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)

  const handlePage = (page) => {
    if (page >= 1 && page <= totalPages) setCurrentPage(page)
  }

  const buildPageNumbers = () => {
    const pages = []
    const window = 3
    for (let i = 1; i <= Math.min(window, totalPages); i++) pages.push(i)
    if (totalPages > window + 1) pages.push('...')
    if (totalPages > window) pages.push(totalPages)
    return pages
  }

  return (
    <div className="reports-page">
      <div className="reports-heading">
        <h1 className="reports-title">Reports List</h1>
        <p className="reports-subtitle">
          Detailed overview of your vulnerability assessments and automated scans.
        </p>
      </div>

      <div className="reports-card">
        {loading ? (
          <div className="reports-state">Loading…</div>
        ) : error ? (
          <div className="reports-state reports-state--error">Error: {error}</div>
        ) : reports.length === 0 ? (
          <div className="reports-state">No reports found.</div>
        ) : (
          <table className="reports-table">
            <thead>
              <tr>
                <th>FILE / URL</th>
                <th>STATUS</th>
                <th>TOTAL FINDINGS</th>
                <th>PROGRESS</th>
                <th>CREATED AT</th>
                <th>ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {pageReports.map((report) => {
                const pct = parseProgress(report.progress, report.processed_findings, report.total_findings)
                return (
                  <tr key={report.id}>
                    <td className="col-file">
                      <div className="file-cell">
                        <FileIcon fileName={report.file_name} />
                        <span className="file-name">{report.file_name}</span>
                      </div>
                    </td>
                    <td className="col-status">
                      <StatusBadge status={report.status} />
                    </td>
                    <td className="col-findings">{report.total_findings}</td>
                    <td className="col-progress">
                      <ProgressBar value={pct} />
                    </td>
                    <td className="col-date">{formatDate(report.created_at)}</td>
                    <td className="col-actions">
                      <a href="#" className="action-link" onClick={(e) => { e.preventDefault(); handleViewDetails(report) }}>
                        View Details
                      </a>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}

        {!loading && !error && reports.length > 0 && (
          <div className="reports-pagination">
            <span className="pagination-info">
              Showing {(currentPage - 1) * PAGE_SIZE + 1} to{' '}
              {Math.min(currentPage * PAGE_SIZE, reports.length)} of {reports.length} reports
            </span>
            <div className="pagination-controls">
              <button
                className="page-btn page-btn--arrow"
                onClick={() => handlePage(currentPage - 1)}
                disabled={currentPage === 1}
              >
                <ChevronLeft />
              </button>
              {buildPageNumbers().map((p, idx) =>
                p === '...' ? (
                  <span key={`e-${idx}`} className="page-ellipsis">…</span>
                ) : (
                  <button
                    key={p}
                    className={`page-btn${currentPage === p ? ' page-btn--active' : ''}`}
                    onClick={() => handlePage(p)}
                  >
                    {p}
                  </button>
                )
              )}
              <button
                className="page-btn page-btn--arrow"
                onClick={() => handlePage(currentPage + 1)}
                disabled={currentPage === totalPages}
              >
                <ChevronRight />
              </button>
            </div>
          </div>
        )}
      </div>

      <ReportDrawer report={selectedReport} loading={loadingDetail} onClose={() => setSelectedReport(null)} />

      <div className="reports-footer-banner">
        <span className="footer-dot">●</span>
        <span>NEED ASSISTANCE WITH REPORT ANALYSIS? CONTACT SUPPORT</span>
      </div>
    </div>
  )
}

export default ReportsList
