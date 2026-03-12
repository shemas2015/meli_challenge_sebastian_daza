# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Automated vulnerability triage system using CrewAI multi-agent AI pipeline. Analyzes security vulnerability reports through static code analysis, dynamic payload testing, and LLM-driven triage to classify findings as TRUE_POSITIVE, FALSE_POSITIVE, or INCONCLUSIVE.

## Commands

### Running the Application
```bash
# Start all services (PostgreSQL, Django backend, OWASP Juice Shop)
docker-compose up -d

# Apply migrations after container start
docker-compose exec backend python manage.py migrate

# Local development server (uses SQLite)
python manage.py runserver
```

### Database
```bash
python manage.py migrate
python manage.py makemigrations
```

### Testing & Code Quality
```bash
pytest                          # Run all tests
pytest vulnerabilities/tests.py # Run specific test file
pytest --cov=vulnerabilities    # With coverage
black .                         # Format code
flake8 .                        # Lint
mypy vulnerabilities/           # Type check
```

## Architecture

### Analysis Pipeline

```
POST /api/vulnerabilities/analyze
  → VulnerabilityAnalysisService (services.py)
      → StaticAnalyzer (optional, regex-based)
      → DynamicAnalyzer (optional, HTTP payloads)
      → AgentOrchestrator (orchestrator.py)
          → ParserAgent → [StaticAnalyzerAgent] → [DynamicValidatorAgent] → TriageAgent
  → AnalysisResult saved to DB
```

**Three analysis modes:**
1. **Static only** — source code available, no running app
2. **Dynamic only** — running app available, no source code
3. **Combined** — both (highest confidence)

### Key Directories

- [vulnerabilities/agents/](vulnerabilities/agents/) — CrewAI agent implementations. `base.py` has the LLM provider factory; `orchestrator.py` coordinates the sequential pipeline.
- [vulnerabilities/static_analysis/](vulnerabilities/static_analysis/) — Regex pattern matching per vulnerability type (SQL injection, XSS, CSRF, IDOR, path traversal).
- [vulnerabilities/dynamic_analysis/](vulnerabilities/dynamic_analysis/) — HTTP payload execution against target URLs and response analysis.
- [vulnerabilities/repositories/](vulnerabilities/repositories/) — Read-only data access layer (repository pattern).

### Models (vulnerabilities/models.py)

- `VulnerabilityReport` — input: type, endpoint, method, parameter, payload, target_url
- `AnalysisResult` — output: validation_status, severity, confidence_score, agent_reasoning, static/dynamic JSON results
- `AgentExecution` — per-agent trace: prompts, responses, tokens used

### LLM Configuration

Configured via environment variables. Provider selected in `agents/base.py`. Supports:
- Anthropic (Claude) — `ANTHROPIC_API_KEY`
- OpenAI (GPT-4) — `OPENAI_API_KEY`
- Google (Gemini) — `GOOGLE_API_KEY`

Current `.env.example` shows the required variables. Agents use `temperature=0.1` for deterministic output and expect JSON wrapped in markdown code blocks.

### API Endpoints

- `POST /api/vulnerabilities/analyze` — main entry point
- `GET /api/vulnerabilities/reports/` — list/filter reports
- `GET /api/vulnerabilities/analyses/` — list/filter results
- `GET /api/docs/` — Swagger UI
- `GET /api/redoc/` — ReDoc

### Infrastructure

- Django 5.x + Django REST Framework + drf-spectacular (OpenAPI)
- PostgreSQL in Docker; SQLite for local dev
- OWASP Juice Shop on port 3000 as test target
- Backend API on port 8000
