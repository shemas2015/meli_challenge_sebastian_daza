# GenAI Vulnerability Triage Solution



## Roadmap
The [ROADMAP.md](ROADMAP.md) file documents the planning and exploration phase, demonstrating a structured development approach with 7 phases, timeline estimation, and technology selection before implementation.


## Quick Start

Start all services:
```bash
docker-compose up -d
```

Services:
- **Frontend** (http://localhost:5174) - React dashboard
- **Backend API** (http://localhost:8000) - Django REST API with AI agents for vulnerability triage
- **OWASP Juice Shop** (http://localhost:3000) - Vulnerable web application for testing
- **PostgreSQL** (localhost:5432) - Database for storing analysis results

Run migrations (first time or after model changes):
```bash
docker-compose exec backend python manage.py migrate
```

Stop services:
```bash
docker-compose down
```

## Frontend

React dashboard (`frontend/`) served by nginx via Docker. Built with Vite + plain CSS, no UI framework.

**Configuring the backend URL**

The frontend calls the backend API at build time via the `VITE_API_URL` environment variable. Vite bakes this value into the static bundle — it cannot be changed at runtime without rebuilding.

In `docker-compose.yml`:
```yaml
frontend:
  build:
    args:
      VITE_API_URL: http://<your-host>:8000   # change this to match your backend address
```

After changing it, rebuild:
```bash
docker-compose up -d --build frontend
```

For local development outside Docker:
```bash
# frontend/.env
VITE_API_URL=http://localhost:8000
```
Then run `npm run dev` inside `frontend/`.

**CORS** is enabled on the backend (`CORS_ALLOW_ALL_ORIGINS = True` in `settings.py`) so the browser can reach the API from any origin.

## AI Agent System

Multi-agent system for automated vulnerability triage using AI agents.

### PDF Upload Pipeline (primary flow)

Upload a scanner report PDF and the system processes all findings automatically in a background thread:

```
POST /api/vulnerabilities/upload   (multipart/form-data, field: file)
            │
            ▼
    ScanReportUploadView
    Extract text from PDF (pypdf)
    Create ScanReport → start background thread → HTTP 202
            │
            ▼  (background)
╔══════════════════════════════════════════════╗
║       PDF PARSER AGENT  (CrewAI)             ║
║  Reads raw PDF text → returns JSON array     ║
║  of all vulnerability findings               ║
╚══════════════════════════════════════════════╝
            │
            ▼  for each finding
    validate_finding()
    ┌────────────────────┬─────────────────────┐
    │  can_auto_test     │  missing fields/type │
    ▼                    ▼                      │
analyze_vulnerability   Save VulnerabilityReport│
(dynamic only)          can_auto_test=False     │
                        skip_reason=<why>       │
    └────────────────────┴─────────────────────┘
            │
            ▼
    ScanReport.status = COMPLETED

GET /api/vulnerabilities/upload/<id>/   → check progress ("3/5")
```

### Per-Finding Triage Pipeline
meli
For each auto-testable finding:

```
DynamicAnalyzer (HTTP probe with payload)
        │
        ▼
╔══════════════════════════════════════════════╗
║  Parser → [Static Analyzer] → [Dynamic       ║
║            Validator]        → Triage Agent  ║
╚══════════════════════════════════════════════╝
        │
        ▼
AnalysisResult: TRUE_POSITIVE / FALSE_POSITIVE / INCONCLUSIVE
```

### Agents

| Agent | File | Role |
|---|---|---|
| PDF Parser | `agents/pdf_parser_agent.py` | Extracts structured findings from raw PDF text |
| Parser | `agents/orchestrator.py` | Structures vulnerability data for analysis |
| Static Analyzer | `agents/static_analyzer_agent.py` | Reviews regex scan results on source code |
| Dynamic Validator | `agents/dynamic_validator_agent.py` | Reviews HTTP probe results |
| Triage | `agents/triage_agent.py` | Synthesizes all evidence → final verdict |

### Analysis Modes (per finding)

**Dynamic Only** (default for PDF uploads)
- **Agents used**: Parser → Dynamic Validator → Triage

**Static Only** (source code available, no running app)
- **Agents used**: Parser → Static Analyzer → Triage

**Combined** (highest confidence)
- **Agents used**: Parser → Static Analyzer → Dynamic Validator → Triage