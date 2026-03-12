import React from 'react'
import './ReportDrawer.css'

const ValidationBadge = ({ status }) => {
  if (!status) return <span className="drawer-badge drawer-badge--none">—</span>
  const cls =
    status === 'TRUE_POSITIVE'  ? 'drawer-badge drawer-badge--true-positive' :
    status === 'FALSE_POSITIVE' ? 'drawer-badge drawer-badge--false-positive' :
                                  'drawer-badge drawer-badge--inconclusive'
  return <span className={cls}>{status.replace('_', ' ')}</span>
}

const SeverityBadge = ({ severity }) => {
  if (!severity) return <span className="drawer-badge drawer-badge--none">—</span>
  const cls =
    severity === 'CRITICAL' ? 'drawer-badge drawer-badge--critical' :
    severity === 'HIGH'     ? 'drawer-badge drawer-badge--high' :
    severity === 'MEDIUM'   ? 'drawer-badge drawer-badge--medium' :
    severity === 'LOW'      ? 'drawer-badge drawer-badge--low' :
                              'drawer-badge drawer-badge--info'
  return <span className={cls}>{severity}</span>
}

function ReportDrawer({ report, loading, onClose }) {
  if (!report && !loading) return null

  if (loading) return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-header">
          <div className="drawer-title-group">
            <span className="drawer-label">Loading…</span>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
          </button>
        </div>
        <div className="drawer-body"><p className="drawer-empty">Fetching details…</p></div>
      </aside>
    </>
  )

  const findings = report.vulnerability_reports || []

  return (
    <>
      <div className="drawer-backdrop" onClick={onClose} />
      <aside className="drawer">
        <div className="drawer-header">
          <div className="drawer-title-group">
            <span className="drawer-label">Scan Report #{report.id}</span>
            <h2 className="drawer-title">{report.file_name}</h2>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
            </svg>
          </button>
        </div>

        <div className="drawer-meta">
          <div className="drawer-meta-item">
            <span className="drawer-meta-label">Status</span>
            <span className={`drawer-status drawer-status--${report.status.toLowerCase()}`}>{report.status}</span>
          </div>
          <div className="drawer-meta-item">
            <span className="drawer-meta-label">Findings</span>
            <span className="drawer-meta-value">{report.total_findings}</span>
          </div>
          <div className="drawer-meta-item">
            <span className="drawer-meta-label">Progress</span>
            <span className="drawer-meta-value">{report.progress}</span>
          </div>
        </div>

        <div className="drawer-body">
          <h3 className="drawer-section-title">
            Vulnerability Findings
            <span className="drawer-count">{findings.length}</span>
          </h3>

          {findings.length === 0 ? (
            <p className="drawer-empty">No findings available.</p>
          ) : (
            <div className="drawer-findings">
              {findings.map((f) => (
                <div key={f.id} className="finding-card">
                  <div className="finding-card-header">
                    <span className="finding-type">{f.type.replace(/_/g, ' ')}</span>
                    <div className="finding-badges">
                      <ValidationBadge status={f.validation_status} />
                      <SeverityBadge severity={f.severity} />
                    </div>
                  </div>

                  <div className="finding-row">
                    <span className="finding-label">Endpoint</span>
                    <code className="finding-code">{f.method} {f.endpoint}</code>
                  </div>

                  {f.parameter && (
                    <div className="finding-row">
                      <span className="finding-label">Parameter</span>
                      <code className="finding-code">{f.parameter}</code>
                    </div>
                  )}

                  {f.payload && (
                    <div className="finding-row">
                      <span className="finding-label">Payload</span>
                      <code className="finding-code finding-code--payload">{f.payload}</code>
                    </div>
                  )}

                  <div className="finding-row finding-row--desc">
                    <span className="finding-label">Description</span>
                    <p className="finding-desc">{f.description}</p>
                  </div>

                  {f.confidence_score != null && (
                    <div className="finding-row">
                      <span className="finding-label">Confidence</span>
                      <span className="finding-desc">{Math.round(f.confidence_score * 100)}%</span>
                    </div>
                  )}

                  {f.agent_reasoning && (
                    <div className="finding-row finding-row--desc">
                      <span className="finding-label">Reasoning</span>
                      <p className="finding-desc">{f.agent_reasoning}</p>
                    </div>
                  )}

                  {!f.can_auto_test && f.skip_reason && (
                    <div className="finding-row">
                      <span className="finding-label">Skip reason</span>
                      <span className="finding-skip">{f.skip_reason}</span>
                    </div>
                  )}

                  {f.agent_executions && f.agent_executions.length > 0 && (
                    <details className="finding-executions">
                      <summary className="finding-executions-summary">
                        Agent Executions ({f.agent_executions.length})
                      </summary>
                      <div className="finding-executions-list">
                        {f.agent_executions.map((ex) => (
                          <div key={ex.id} className="exec-item">
                            <span className="exec-agent">{ex.agent_type}</span>
                            {ex.llm_response && (
                              <pre className="exec-response">{ex.llm_response}</pre>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  )
}

export default ReportDrawer
