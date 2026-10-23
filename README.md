# QueryPilot — Agentic AI SQL Analyst

QueryPilot is a production-grade web application that enables users to ask natural language questions over relational databases. It leverages Google Gemini for SQL generation, deterministic AST parsing with SQLGlot, Guardrails AI validation, bounded SQL repair loops, read-only query execution, and LangSmith workflow tracing and evaluation.

---

## Architecture Overview

```text
┌─────────────────────────────────┐
│  React + TypeScript + Tailwind  │
│  Interactive Analyst Dashboard  │
└───────────────┬─────────────────┘
                │ HTTP / JSON
┌───────────────▼─────────────────┐
│  FastAPI Backend Server         │
│  Validation, API, Health        │
└───────────────┬─────────────────┘
                │
┌───────────────▼─────────────────────────────────────┐
│  LangGraph Workflow State Machine                   │
│  Classify → Schema → Generate SQL → Guardrails/AST  │
│  → Repair Loop → Read-only Execution → Analyze      │
│  → Build Chart → Finalize Response                  │
└───────────────┬─────────────────────┬───────────────┘
                │                     │
        ┌───────▼────────┐    ┌───────▼────────┐
        │ PostgreSQL DB  │    │ LangSmith      │
        │ Read-only Role │    │ Observability  │
        └────────────────┘    └────────────────┘
```

---

## Implementation Status (Milestones 1–8 Complete)

- [x] **Milestone 1 — Foundation**: Centralized settings via `pydantic-settings` in `backend/app/config.py`, `.env.example`, FastAPI health check endpoint, React + TypeScript + Tailwind frontend shell, and Dockerfiles.
- [x] **Milestone 2 — Database**: SQLAlchemy 2.x ORM models (`customers`, `products`, `orders`, `order_items`), idempotent synthetic retail demo seeder (`demo_seed.py`), schema introspection (`schema_introspection.py`), safe query executor, and read-only PostgreSQL role setup (`setup_permissions.sql`).
- [x] **Milestone 3 — Gemini SQL Generation**: Gemini integration using `ChatGoogleGenerativeAI` with structured output parsing (`GeneratedSQLOutput`) and Guardrails AI validation.
- [x] **Milestone 4 — Safety & Guardrails**: Deterministic SQLGlot AST inspection enforcing single-statement read-only `SELECT` queries, DDL/DML blocking, schema allowlisting, and automatic `LIMIT` row capping.
- [x] **Milestone 5 — LangGraph Workflow**: Typed state machine (`SQLState`), question classifier, bounded retry repair loop (up to 3 attempts), result analyst for grounded explanations, and deterministic chart builder.
- [x] **Milestone 6 — LangSmith Tracing & Evaluation**: Privacy-preserving trace metadata sanitization (zero secrets or raw connection leaks) and a 22-case benchmark evaluation suite (`runner.py`) achieving 100% unsafe query rejection.
- [x] **Milestone 7 — Interactive Frontend**: Full analyst dashboard with natural language query input, copyable SQL dark panel, responsive data tables, dynamic horizontal/line charts, safety status breakdown, and database schema drawer.
- [x] **Milestone 8 — Quality & Verification**: 51 automated backend unit and integration tests passing with 100% pass rate, zero-error frontend TypeScript production build, and Docker Compose orchestration.

---

## Prerequisites

- **Python**: 3.11+ (Python 3.13 tested)
- **Node.js**: v18+ (tested on Node v22.19.0)
- **npm**: 9+ (tested on npm 10.9.3)
- **Git**
- **PostgreSQL**: (optional for local non-Docker development; SQLite fallback supported in tests)

---

## Quick Start Guide

### 1. Environment Configuration

Copy `.env.example` to `backend/.env`:

```bash
cp .env.example backend/.env
```

Configure your environment variables in `backend/.env`:
```dotenv
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=querypilot-dev

DATABASE_URL=postgresql+psycopg2://querypilot_readonly:change_me@localhost:5432/querypilot
DATABASE_DIALECT=postgres
QUERY_TIMEOUT_SECONDS=10
MAX_ROWS=500
MAX_SQL_REPAIR_ATTEMPTS=3
```

### 2. Database Setup & Seeding

To set up the dedicated least-privilege read-only role in PostgreSQL:

```bash
psql -U postgres -d querypilot -f backend/app/database/setup_permissions.sql
```

To seed the synthetic retail demo dataset (customers, products, orders, order_items):

```bash
# Using python module
python -m app.database.demo_seed
```

### 3. Backend Setup & Run

From the repository root:

```bash
# Activate virtual environment
.\venv\Scripts\activate   # Windows PowerShell
# source venv/bin/activate # Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# Run all 51 automated tests
pytest backend/tests -v

# Run the evaluation benchmark suite
python -m app.evaluation.runner

# Start FastAPI development server
uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000
```

FastAPI interactive documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Frontend Setup & Run

In a separate terminal:

```bash
cd frontend

# Install dependencies
npm install

# Build production bundle
npm run build

# Start Vite development server
npm run dev
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

---

## API Endpoints

### `GET /api/health`
Returns readiness checks without revealing any secrets or credentials.

### `GET /api/schema`
Returns approved analytical table metadata and the canonical revenue calculation business rule.

### `POST /api/query`
Executes natural-language questions through the LangGraph agentic workflow:
```json
{
  "question": "Which five products generated the most revenue last quarter?"
}
```

Response payload:
```json
{
  "request_id": "3b29c9a0-62eb-4581-ba24-001096a6c0ea",
  "question": "Which five products generated the most revenue last quarter?",
  "sql": "SELECT p.product_name, SUM(oi.quantity * oi.unit_price - oi.discount_amount) AS revenue FROM products p ... LIMIT 5",
  "columns": ["product_name", "revenue"],
  "rows": [...],
  "insight": "The top revenue generator was UltraBook Pro 15 with $14,249.85 in total sales.",
  "chart": {
    "type": "bar",
    "title": "Revenue by Product Name",
    "x": "product_name",
    "y": "revenue"
  },
  "validation": {
    "status": "passed",
    "messages": []
  },
  "execution": {
    "duration_ms": 14,
    "row_count": 5,
    "truncated": false
  },
  "trace": {
    "project": "querypilot-dev",
    "url": null
  }
}
```

---

## Security Guarantees

1. **Deterministic AST Validation**: SQLGlot parses model output into an abstract syntax tree, rejecting DDL/DML, multi-statement queries, or non-SELECT operations before database execution.
2. **Schema Allowlists**: Only approved tables (`customers`, `products`, `orders`, `order_items`) and columns are allowed. Any attempt to reference unapproved tables or columns is blocked.
3. **Least-Privilege Database Role**: Analytical queries run under `querypilot_readonly`, which has only `SELECT` permissions and enforced statement timeouts.
4. **Zero Secret Leakage**: API keys, passwords, and raw database connection strings are never sent to the client, logged in health checks, or exported to LangSmith metadata.
