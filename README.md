# QueryPilot — Agentic AI SQL Analyst

QueryPilot is a web application that enables users to ask natural language questions over relational databases. It leverages Google Gemini for SQL generation, deterministic AST parsing with SQLGlot, Guardrails AI validation, bounded SQL repair loops, read-only query execution, and LangSmith workflow tracing and evaluation.

---

## Architecture Overview

```text
┌─────────────────────────────────┐
│  React + TypeScript + Tailwind  │
│  Analyst Dashboard UI           │
└───────────────┬─────────────────┘
                │ HTTP / JSON
┌───────────────▼─────────────────┐
│  FastAPI Backend Server         │
│  Validation, API, Health        │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────────────────────────┐
│  LangGraph Workflow (Milestones 3–5)                │
│  Classify → Schema → Generate SQL → Guardrails/AST  │
│  → Repair Loop → Read-only Execution → Analyze      │
└───────────────┬─────────────────────┬───────────────┘
                │                     │
        ┌───────▼────────┐    ┌───────▼────────┐
        │ PostgreSQL DB  │    │ LangSmith      │
        │ Read-only Role │    │ Observability  │
        └────────────────┘    └────────────────┘
```

---

## Milestone 1 Implementation Status

- [x] **Repository Foundation & Configuration**: Centralized settings via `pydantic-settings` in `backend/app/config.py` loading `.env` without exposing secrets.
- [x] **Environment Template**: `.env.example` documenting all configuration keys with safe placeholders.
- [x] **FastAPI Health Endpoint**: `GET /api/health` returning non-sensitive service readiness and component statuses.
- [x] **Automated Test Suite**: Pytest tests in `backend/tests/test_health.py` validating API contracts and verifying zero secret leakage.
- [x] **React + TypeScript + Tailwind Frontend**: Modern Vite-based UI in `frontend/` with real-time health diagnostics and API proxying.
- [x] **Docker Infrastructure**: `backend/Dockerfile`, `frontend/Dockerfile`, and `docker-compose.yml`.

---

## Prerequisites

- **Python**: 3.11+ (Python 3.13 supported)
- **Node.js**: v18+ (tested on Node v22.19.0)
- **npm**: 9+ (tested on npm 10.9.3)
- **Git**

---

## Getting Started

### 1. Environment Setup

Copy `.env.example` to `.env` in the root or `backend/` directory:

```bash
cp .env.example .env
```

Set your configuration values:
- `GOOGLE_API_KEY`: Your Google Gemini API key.
- `GEMINI_MODEL`: `gemini-2.5-flash` (or your preferred Gemini model).
- `DATABASE_URL`: Connection string for PostgreSQL (configured for read-only user in Milestone 2).
- `LANGSMITH_API_KEY`: (Optional) LangSmith API key for workflow tracing.
- `LANGSMITH_TRACING`: Set to `true` to enable tracing or `false` for local offline operation.

### 2. Backend Setup & Run

From the repository root:

```bash
# Activate virtual environment
.\venv\Scripts\activate   # Windows PowerShell
# source venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# Run automated tests
pytest backend/tests -v

# Start FastAPI development server
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

FastAPI docs are available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) and health check at [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health).

### 3. Frontend Setup & Run

In a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser. The frontend automatically proxies `/api/*` requests to the FastAPI backend.

---

## Health Check API Contract

### `GET /api/health`

Response:
```json
{
  "status": "ok",
  "app_env": "development",
  "version": "0.1.0",
  "checks": {
    "gemini_configured": true,
    "gemini_model": "gemini-2.5-flash",
    "database_configured": false,
    "database_dialect": "postgres",
    "langsmith_configured": true
  }
}
```

*Security guarantee: API keys, passwords, and raw database credentials are never included in the health response or logs.*

---

## Upcoming Milestones

- **Milestone 2**: PostgreSQL schema, synthetic retail seed data, schema introspection, and read-only database role.
- **Milestone 3**: Gemini SQL generation and structured output parsing.
- **Milestone 4**: Guardrails AI, SQLGlot AST validation, schema allowlists, and execution timeout/limits.
- **Milestone 5**: LangGraph state machine, conditional repair loop, execution, analysis, and chart generation.
- **Milestone 6**: LangSmith tracing, evaluation dataset (20+ questions), and benchmark runner.
- **Milestone 7**: Interactive analyst frontend with SQL panel, data tables, Plotly charts, and trace inspection.
- **Milestone 8**: Production hardening, Docker Compose integration tests, and deployment verification.
