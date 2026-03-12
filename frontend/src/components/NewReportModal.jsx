import React, { useState, useRef } from 'react'
import './NewReportModal.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://100.93.112.98:8000'

const GlobeIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
  </svg>
)

const LockIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z" />
  </svg>
)

const UploadIcon = () => (
  <svg width="32" height="32" viewBox="0 0 24 24" fill="currentColor">
    <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11zM8 15h2.5v2.5h3V15H16l-4-4-4 4z" />
  </svg>
)

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
  </svg>
)

const PlayIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M8 5v14l11-7z" />
  </svg>
)

const CheckCircleIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z" />
  </svg>
)

const CodeIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
    <path d="M9.4 16.6L4.8 12l4.6-4.6L8 6l-6 6 6 6 1.4-1.4zm5.2 0l4.6-4.6-4.6-4.6L16 6l6 6-6 6-1.4-1.4z" />
  </svg>
)

function NewReportModal({ onClose, onSuccess }) {
  const [activeTab, setActiveTab] = useState('website')
  const [pdfFile, setPdfFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file && file.type === 'application/pdf') {
      setPdfFile(file)
      setError(null)
    } else if (file) {
      setError('Only PDF files are accepted.')
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type === 'application/pdf') {
      setPdfFile(file)
      setError(null)
    } else if (file) {
      setError('Only PDF files are accepted.')
    }
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => setIsDragging(false)

  const handleSubmit = async () => {
    if (!pdfFile) {
      setError('Please upload a PDF report before starting verification.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const formData = new FormData()
      formData.append('file', pdfFile)
      const res = await fetch(`${API_URL}/api/vulnerabilities/upload`, {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      onSuccess && onSuccess()
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <div className="nrm-backdrop" onClick={onClose} />
      <div className="nrm-overlay">
        <div className="nrm-modal" onClick={(e) => e.stopPropagation()}>
          {/* Breadcrumb */}
          <div className="nrm-breadcrumb">
            <span>PROJECT</span>
            <span className="nrm-breadcrumb-sep">›</span>
            <span>Internal Security Audit</span>
          </div>

          {/* Header */}
          <div className="nrm-header">
            <div>
              <h2 className="nrm-title">Scanner Setup</h2>
              <p className="nrm-subtitle">Configure your validation target and initiate the automated security assessment.</p>
            </div>
            <button className="nrm-close" onClick={onClose} aria-label="Close">
              <CloseIcon />
            </button>
          </div>

          {/* Card */}
          <div className="nrm-card">
            {/* Tabs */}
            <div className="nrm-tabs">
              <button
                className={`nrm-tab${activeTab === 'website' ? ' nrm-tab--active' : ''}`}
                onClick={() => setActiveTab('website')}
              >
                <GlobeIcon />
                Validate Website
              </button>
              <button
                className="nrm-tab nrm-tab--disabled"
                disabled
                title="Source code validation is not available"
              >
                <CodeIcon />
                Source Code
              </button>
            </div>

            {/* Tab content */}
            <div className="nrm-tab-content">
              {/* Left column */}
              <div className="nrm-left">
                {/* Target URL */}
                <div className="nrm-field">
                  <label className="nrm-label">Target URL</label>
                  <div className="nrm-url-input">
                    <span className="nrm-url-text">http://juice-shop:3000</span>
                    <span className="nrm-url-lock"><LockIcon /></span>
                  </div>
                  <p className="nrm-field-hint">URL is locked to the current project environment.</p>
                </div>

                {/* PDF Report Upload */}
                <div className="nrm-field">
                  <label className="nrm-label">Security Report (PDF)</label>
                  <div
                    className={`nrm-dropzone${isDragging ? ' nrm-dropzone--drag' : ''}${pdfFile ? ' nrm-dropzone--filled' : ''}`}
                    onClick={() => fileInputRef.current.click()}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                  >
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="application/pdf"
                      style={{ display: 'none' }}
                      onChange={handleFileChange}
                    />
                    {pdfFile ? (
                      <div className="nrm-dropzone-filled">
                        <span className="nrm-dropzone-file-icon">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z" />
                          </svg>
                        </span>
                        <div>
                          <p className="nrm-dropzone-name">{pdfFile.name}</p>
                          <p className="nrm-dropzone-size">{(pdfFile.size / 1024).toFixed(1)} KB</p>
                        </div>
                        <button
                          className="nrm-dropzone-remove"
                          onClick={(e) => { e.stopPropagation(); setPdfFile(null) }}
                          title="Remove file"
                        >
                          <CloseIcon />
                        </button>
                      </div>
                    ) : (
                      <div className="nrm-dropzone-empty">
                        <span className="nrm-dropzone-icon"><UploadIcon /></span>
                        <p className="nrm-dropzone-text">Drop your PDF report here or <span className="nrm-dropzone-link">browse</span></p>
                        <p className="nrm-dropzone-hint">Accepts PDF security incident reports</p>
                      </div>
                    )}
                  </div>
                </div>

                {error && <p className="nrm-error">{error}</p>}
              </div>

              {/* Right column */}
              <div className="nrm-right">
                <div className="nrm-info-box">
                  <p className="nrm-info-title">
                    <span className="nrm-info-icon">ℹ</span>
                    Scan Information
                  </p>
                  <ul className="nrm-info-list">
                    <li><CheckCircleIcon /> Estimated duration: 15-20 minutes</li>
                    <li><CheckCircleIcon /> Validates XSS, SQLi, and CSRF vulnerabilities</li>
                    <li><CheckCircleIcon /> Automated report generation upon completion</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="nrm-footer">
              <span className="nrm-last-scan">🕐 Last scan: 2 days ago</span>
              <button
                className="nrm-btn-start"
                onClick={handleSubmit}
                disabled={submitting}
              >
                <PlayIcon />
                {submitting ? 'Starting…' : 'Start Verification'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default NewReportModal
