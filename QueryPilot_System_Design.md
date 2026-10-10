# QueryPilot — System Design & Implementation Specification

**Document type:** System Design and Build Instructions  
**Project:** QueryPilot — Agentic AI SQL Analyst  
**Version:** 1.0  
**Purpose:** This document is the source of truth for building QueryPilot in Antigravity. Implement the project in working, testable milestones. Do not generate a superficial mock-up or leave core features as TODOs.

---

## 1. Product Overview

QueryPilot is a web application that lets users ask questions about a relational database in natural language. It generates SQL using the Gemini API, validates it with deterministic SQL checks and Guardrails AI, executes only safe read-only queries, analyzes returned data, and presents results with an explanation and optional chart.

The application must be observable: LangSmith should trace the LangGraph workflow and support evaluation of SQL correctness, guardrail behavior, latency, and answer quality.

### Example user journey

User asks: “Which five products generated the most revenue last quarter?”

QueryPilot should:
1. Inspect the database schema and identify relevant tables/columns.
2. Generate a SQL query with Gemini.
3. Validate structured output and SQL safety.
4. Check that referenced tables and columns exist.
5. If validation fails, repair the query with a bounded retry loop.
6. Execute the query using a read-only database account and enforce a timeout/row limit.
7. Analyze the returned rows without inventing facts.
8. Return the answer, SQL, tabular results, and a suitable chart when useful.
9. Record the workflow in LangSmith, without logging secrets or unnecessarily sensitive row data.

### Product principles

- **LLM interprets; deterministic code enforces and computes.**
- Never trust model-generated SQL merely because it looks valid.
- Safety checks must be enforced in code and database permissions, not only by prompts.
- Use bounded retries and predictable error states.
- Show users the generated SQL and validation status.
- Treat database results as the source of truth; explanations must be grounded in those results.
- Build a functional vertical slice first, then add features incrementally.

---

## 2. Technology Stack

### Frontend
- React with TypeScript
- Vite
- Tailwind CSS
- Plotly.js (or `react-plotly.js`) for charts
- A clean, responsive analyst dashboard

### Backend
- Python 3.11 or newer
- FastAPI
- Pydantic for request/response models
- SQLAlchemy 2.x
- PostgreSQL as the primary supported database
- MySQL may be supported through a configurable SQLAlchemy connection URL, but PostgreSQL is the first implementation target

### AI and workflow
- Google Gemini API through `langchain-google-genai`
- LangGraph for stateful workflow orchestration and conditional routing
- Guardrails AI for structured-output validation and custom validation integration
- SQLGlot for SQL parsing, statement classification, and dialect-aware checks
- LangSmith for traces, debugging, and evaluations

### Developer experience and testing
- `pytest`
- `httpx` for API tests
- Ruff for linting/formatting
- Docker and Docker Compose for reproducible local setup
- `.env.example` for documented configuration

Use compatible, current stable package versions and pin them in dependency files after verifying installation. Do not invent package APIs. If an API has changed, consult the installed package documentation and implement the supported interface.

---

## 3. High-Level Architecture

```text
┌───────────────────────────────┐
│ React + TypeScript + Tailwind │
│ Question / SQL / Results / UI │
└───────────────┬───────────────┘
                │ HTTPS/JSON
┌───────────────▼───────────────┐
│ FastAPI                       │
│ Validation, API, error mapping│
└───────────────┬───────────────┘
                │
┌───────────────▼───────────────────────────────────┐
│ LangGraph workflow                                │
│                                                   │
│ classify_question → get_schema → generate_sql     │
│                                     ↓             │
│                         Guardrails + SQLGlot      │
│                                     ↓             │
│                         schema/safety validation  │
│                              ↙          ↘         │
│                         repair       execute SQL  │
│                              ↘          ↓         │
│                               validate result     │
│                                      ↓            │
│                              analyze results      │
│                                      ↓            │
│                              chart configuration  │
│                                      ↓            │
│                               final response      │
└──────────────────┬────────────────────┬───────────┘
                   │                    │
          ┌────────▼────────┐  ┌────────▼────────┐
          │ PostgreSQL      │  │ LangSmith       │
          │ Read-only role  │  │ Traces/evaluate │
          └─────────────────┘  └─────────────────┘
```

### Trust boundaries

- The browser never receives Gemini or LangSmith API keys.
- The backend is the only component allowed to connect to the database.
- The database connection used for analytical queries must have read-only permissions.
- Model output is untrusted input until it passes deterministic validation.
- LangSmith traces must not include credentials, connection strings, full environment variables, or unrestricted sensitive data.

---

## 4. Repository Structure

Create a monorepo with the following structure:

```text
querypilot/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── health.py
│   │   │   │   ├── query.py
│   │   │   │   └── schema.py
│   │   │   └── schemas.py
│   │   ├── graph/
│   │   │   ├── state.py
│   │   │   ├── nodes.py
│   │   │   ├── routing.py
│   │   │   └── workflow.py
│   │   ├── agents/
│   │   │   ├── sql_generator.py
│   │   │   ├── sql_repair.py
│   │   │   ├── result_analyst.py
│   │   │   └── chart_builder.py
│   │   ├── guardrails/
│   │   │   ├── output_models.py
│   │   │   ├── sql_validator.py
│   │   │   └── guardrail_service.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── schema_introspection.py
│   │   │   ├── query_executor.py
│   │   │   └── demo_seed.py
│   │   ├── services/
│   │   │   ├── query_service.py
│   │   │   └── tracing.py
│   │   └── utils/
│   │       ├── errors.py
│   │       └── logging_config.py
│   └── tests/
│       ├── test_health.py
│       ├── test_sql_validator.py
│       ├── test_query_executor.py
│       ├── test_graph_routing.py
│       └── test_query_api.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── api/client.ts
        ├── types.ts
        ├── components/
        │   ├── AppHeader.tsx
        │   ├── QuestionInput.tsx
        │   ├── SqlViewer.tsx
        │   ├── ResultsTable.tsx
        │   ├── ResultsChart.tsx
        │   ├── InsightPanel.tsx
        │   ├── ValidationStatus.tsx
        │   ├── TraceInfo.tsx
        │   └── LoadingState.tsx
        └── styles/
            └── index.css
```

Keep modules focused and avoid placing all logic in `main.py` or one giant component.

---

## 5. Configuration and Secrets

Use environment variables loaded by a settings module. Include an `.env.example` with placeholders only:

```dotenv
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
FRONTEND_ORIGIN=http://localhost:5173

GOOGLE_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

LANGSMITH_API_KEY=
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=querypilot-dev
LANGSMITH_ENDPOINT=https://api.smith.langchain.com

DATABASE_URL=postgresql+psycopg://querypilot_readonly:change_me@localhost:5432/querypilot
DATABASE_DIALECT=postgres
QUERY_TIMEOUT_SECONDS=10
MAX_ROWS=500
MAX_SQL_REPAIR_ATTEMPTS=3
```

Requirements:
- Never commit `.env`.
- Validate required settings at startup and show a clear configuration error without exposing secret values.
- Keep secrets server-side.
- Use the currently supported LangSmith environment variable names; document any naming differences in the installed version.
- Gemini is the model provider. LangSmith is the tracing/evaluation platform, not the LLM provider.
- Do not log API keys or the complete database URL.
- If LangSmith is not configured, allow local development to continue with tracing disabled and display a non-blocking warning.

---

## 6. Database Design and Demo Data

Use PostgreSQL as the default database. Provide a script to create and seed a small synthetic retail dataset. Do not use real personal data.

Suggested tables:

### `customers`
- `id` (primary key)
- `customer_name`
- `region`
- `city`
- `created_at`

### `products`
- `id` (primary key)
- `product_name`
- `category`
- `unit_price`

### `orders`
- `id` (primary key)
- `customer_id` (foreign key)
- `order_date`
- `status`

### `order_items`
- `id` (primary key)
- `order_id` (foreign key)
- `product_id` (foreign key)
- `quantity`
- `unit_price`
- `discount_amount`

Revenue should be defined consistently as `quantity * unit_price - discount_amount` for the demo dataset. Document this definition in the README and schema context. Avoid ambiguous references to a nonexistent `revenue` column.

Seed enough synthetic records to demonstrate grouping, filtering, trends, and joins. Include varied dates and regions. Make the seed script idempotent or clearly document how to reset the demo database.

### Database permissions
- Create a separate read-only database role for the application.
- Grant only `CONNECT`, schema usage, and `SELECT` on approved analytical tables.
- Do not use an owner/admin connection for executing model-generated SQL.
- Use parameterized statements for any values supplied outside generated SQL.
- Apply statement timeout, maximum returned rows, and request timeout.

---

## 7. API Contract

Implement these endpoints.

### `GET /api/health`
Returns service status and non-sensitive configuration readiness, such as whether the database and model key are configured. Never return secret values.

### `GET /api/schema`
Returns approved table/column metadata that can safely be displayed to the current user.

### `POST /api/query`
Request:

```json
{
  "question": "Which five products generated the most revenue last quarter?"
}
```

Response shape:

```json
{
  "request_id": "server-generated-id",
  "question": "Which five products generated the most revenue last quarter?",
  "sql": "SELECT ...",
  "columns": ["product_name", "revenue"],
  "rows": [],
  "insight": "A concise explanation grounded in the returned rows.",
  "chart": {
    "type": "bar",
    "title": "Revenue by Product",
    "x": "product_name",
    "y": "revenue"
  },
  "validation": {
    "status": "passed",
    "messages": []
  },
  "execution": {
    "duration_ms": 0,
    "row_count": 0,
    "truncated": false
  },
  "trace": {
    "project": "querypilot-dev",
    "url": null
  }
}
```

`trace.url` may be null if a trace URL cannot safely be generated. Do not fabricate a LangSmith URL. Return meaningful HTTP errors for invalid input, validation failure, database timeout, model provider failure, and unexpected errors. Never return stack traces to end users.

Set a reasonable maximum question length, such as 2,000 characters. Add CORS restricted to the configured frontend origin.

---

## 8. LangGraph Workflow

Use a typed state object, for example:

```python
class SQLState(TypedDict, total=False):
    request_id: str
    question: str
    schema_context: str
    sql: str
    validation_errors: list[str]
    validation_status: str
    retry_count: int
    query_rows: list[dict]
    columns: list[str]
    result_summary: str
    insight: str
    chart: dict
    execution_duration_ms: int
    truncated: bool
    fatal_error: str
```

Implement the following graph nodes:

1. `classify_question`: Determine whether the request is a supported data question. If ambiguous, request clarification or return a safe validation message; do not generate SQL for unrelated requests.
2. `get_schema`: Fetch only approved table and column metadata. Cache schema metadata briefly if appropriate.
3. `generate_sql`: Call Gemini with the question, schema, dialect, revenue definition, and strict read-only instructions.
4. `validate_output`: Validate the model's structured response and extract SQL. Reject empty or malformed output.
5. `validate_sql`: Use Guardrails AI and deterministic SQLGlot checks. Verify exactly one permitted read-only query, approved tables, approved columns, and allowed functions where practical.
6. `route_after_validation`: Continue to execution on success; route to repair on correctable failure; stop after the configured maximum retries.
7. `repair_sql`: Ask Gemini to repair SQL using the validation errors and original schema. Do not remove safety constraints.
8. `execute_sql`: Execute only after validation, using the read-only connection, statement timeout, row limit, and execution timing.
9. `analyze_results`: Use Gemini to summarize the results. Provide only bounded result data and explicit instructions not to invent values or conclusions.
10. `build_chart`: Produce a validated chart configuration only when columns and data are suitable.
11. `finalize_response`: Construct the typed API result and validation/execution metadata.

Use conditional edges for repair and failure routing. Limit repair attempts to `MAX_SQL_REPAIR_ATTEMPTS` (default 3). Never let an invalid query reach the executor. Catch errors at node boundaries and return safe, actionable messages.

### State and privacy
- Do not store database credentials in graph state.
- Avoid storing full sensitive result rows in LangSmith metadata.
- Avoid passing unnecessary row data to Gemini. Aggregate or cap rows where possible.
- Do not treat model-provided chart keys, SQL, or table names as trusted.

---

## 9. Guardrails AI and SQL Safety

Guardrails AI is one layer, not the sole security mechanism. Combine it with SQLGlot, schema allowlists, database permissions, and execution limits.

### Structured model output
Define a Pydantic model for SQL generation output, such as:
- `sql: str`
- `explanation: str`
- `assumptions: list[str]`
- `confidence: float` constrained to 0–1

Use Guardrails AI to validate structured output through a supported, documented integration. If the installed Guardrails package API differs from examples, inspect the installed docs and implement the actual current interface. Do not fake a Guardrails integration with a class that is never called.

### Deterministic SQL validation
Use SQLGlot with the configured SQL dialect. Enforce all of the following before execution:

- Exactly one SQL statement.
- Only `SELECT` or a `WITH` query whose final statement is a `SELECT`.
- Reject data-definition and data-manipulation operations, including `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `CREATE`, `GRANT`, `REVOKE`, and database/session-changing commands.
- Reject multiple statements, comments or obfuscation patterns that bypass policy, and unsupported syntax.
- Parse the SQL AST and verify referenced tables and columns against the approved schema.
- Reject wildcard selection where it could expose excessive data, or explicitly constrain its use.
- Add a default maximum row count and database-side statement timeout.
- Add a final `LIMIT` when appropriate, without changing query semantics incorrectly; if the query uses aggregates, still cap returned rows.
- Never rely only on searching the SQL string for forbidden keywords; use AST parsing and database permissions.
- Treat SQL validation failure as a hard stop unless the bounded repair path is used.
- Never auto-execute a suggested index creation or any other write/DDL statement.

The executor must re-validate the SQL immediately before execution. The database's read-only role remains the final safety boundary.

### Guardrail outcomes
Use explicit outcomes such as:
- `passed`
- `rejected_unsafe_sql`
- `rejected_invalid_sql`
- `rejected_unknown_schema_reference`
- `repair_attempted`
- `repair_limit_reached`

Do not present an arbitrary LLM confidence number as a calibrated probability. If shown, label it as a model-estimated confidence and explain that it is not a correctness guarantee. Prefer evidence-based validation indicators.

---

## 10. Gemini Integration

Use `langchain-google-genai` to access Gemini through the backend. Keep model name configurable with `GEMINI_MODEL`; use a currently available model supported by the installed package and API account.

Requirements:
- Use low temperature for SQL generation.
- Use separate prompts for SQL generation, SQL repair, and result analysis.
- Supply only the relevant schema and business definitions.
- Require structured output where supported, and validate it server-side regardless.
- Handle rate limits, timeouts, empty responses, and provider errors gracefully.
- Never allow model output to choose arbitrary database connections or execute tools outside the approved workflow.
- Do not put API keys into prompts or LangSmith metadata.

---

## 11. LangSmith Tracing and Evaluation

Enable LangSmith tracing for the LangGraph run. Use a clear project name such as `querypilot-dev` locally and `querypilot-prod` in production.

Trace meaningful nodes:
- question classification
- schema retrieval
- SQL generation
- Guardrails/SQL validation
- SQL repair attempts
- SQL execution (metadata only where possible)
- result analysis
- chart configuration
- final response

Capture useful metadata:
- request ID
- workflow outcome
- repair count
- validation outcome
- elapsed time
- result row count
- model name
- whether a chart was generated

Do not capture:
- API keys or environment dumps
- database connection strings
- passwords
- unnecessary raw database rows
- sensitive personal data

### Evaluation dataset
Create a repeatable evaluation dataset of at least 20 questions with expected behavior, including:
- straightforward aggregation
- filtering and sorting
- joins
- date ranges
- ambiguous questions
- nonexistent tables/columns
- unsafe requests to modify data
- malformed model output
- empty-result queries
- requests that should be rejected as out of scope

Measure:
- SQL execution success rate
- result correctness against expected answers
- first-attempt validation pass rate
- repair success rate
- unsafe-query rejection rate
- end-to-end latency
- answer groundedness relative to SQL results

Use deterministic test fixtures for correctness. LangSmith traces make failures inspectable; tracing itself does not prove correctness. Provide a script or documented command to run evaluations. Never fabricate evaluation scores in the UI or README.

---

## 12. Frontend UX Requirements

Build a polished, responsive analyst dashboard with a restrained professional design: neutral background, dark text, one consistent accent color, clear spacing, accessible contrast, and no overlapping components. Avoid a generic marketing landing page; the main screen should be the working product.

### Main screen
- App header with QueryPilot branding and API/database status indicators.
- Large natural-language question input and an Analyze button.
- A few clickable example questions.
- Loading state with current workflow stage, if safely available.
- Error state with clear remediation guidance.

### Result view
Use tabs or well-separated panels for:
1. **Answer** — concise natural-language insight.
2. **SQL** — formatted SQL in a dark code panel with copy button.
3. **Data** — responsive table with column headers and empty-state handling.
4. **Chart** — Plotly visualization when the returned chart config is valid.
5. **Validation** — read-only safety status and non-sensitive messages.
6. **Trace** — link only when a real trace URL is available; otherwise show the request/trace identifier and explain that trace access is configured in LangSmith.

Show execution time, number of returned rows, and whether results were truncated. Do not imply that a query was validated if validation did not complete. Ensure the UI is usable on desktop and mobile.

### Frontend behavior
- Send requests only to FastAPI.
- Use typed TypeScript interfaces matching the API schema.
- Disable duplicate submissions while a request is running.
- Preserve the last successful result if a new request fails, but clearly indicate which question it belongs to.
- Never expose API secrets in the frontend bundle.
- Include accessible labels, keyboard focus, and helpful empty/error states.

---

## 13. Error Handling and Reliability

Handle these cases deliberately:
- Missing Gemini key
- Gemini rate limit/provider outage
- LangSmith unavailable
- Database unavailable
- Database statement timeout
- SQL parse failure
- Guardrail rejection
- Unknown table or column
- Repair retry limit reached
- Empty results
- Oversized results
- Unsupported or ambiguous question
- Invalid chart configuration

Use structured server-side logs with request IDs. Return sanitized error messages. Do not retry dangerous or rejected queries by bypassing validation. LangSmith being unavailable must not disable SQL safety. Add a request timeout and bounded model retries.

---

## 14. Testing Requirements

Write automated tests before declaring the project complete.

### Unit tests
- Accept a simple safe `SELECT`.
- Accept a safe aggregate query.
- Accept a safe `WITH ... SELECT` only if SQLGlot confirms the final statement is read-only.
- Reject `DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, and multi-statement SQL.
- Reject unknown tables and columns.
- Reject malformed SQL.
- Verify retry limit and routing.
- Verify chart config references returned columns only.
- Verify analysis handles empty results.

### Integration tests
- Health endpoint returns a valid response.
- Query endpoint validates input.
- Unsafe SQL never reaches the executor.
- Valid SQL executes against a disposable test database.
- Database/model failures return sanitized errors.
- API response matches the declared schema.

Mock Gemini for most automated tests to avoid cost and nondeterminism. Provide an optional live integration test requiring explicit environment configuration.

---

## 15. Docker and Local Development

Provide a Docker Compose setup for PostgreSQL, backend, and frontend where practical. Include a health check for PostgreSQL and a documented startup order. If using a local non-Docker workflow, document the equivalent commands.

The README must explain:
1. Prerequisites.
2. How to create a Gemini API key and configure it.
3. How to configure LangSmith tracing.
4. How to create a database and read-only role.
5. How to seed the demo dataset.
6. How to install and start the backend.
7. How to install and start the frontend.
8. How to run tests and evaluations.
9. Common configuration and connection errors.
10. Known limitations and security boundaries.

Never include real API keys or passwords in the README.

---

## 16. Implementation Plan and Acceptance Criteria

Implement in this order. At the end of each milestone, run tests and keep the application runnable.

### Milestone 1 — Foundation
- Create the repository, settings, FastAPI app, health endpoint, React app, and `.env.example`.
- Add clear setup instructions.
- **Done when:** frontend and backend start locally and health endpoint passes.

### Milestone 2 — Database
- Add PostgreSQL schema, synthetic seed data, schema introspection, and read-only database role documentation.
- **Done when:** backend can list approved schema metadata and execute a fixed safe query.

### Milestone 3 — Gemini SQL generation
- Add Gemini integration and structured output parsing.
- **Done when:** a natural-language question produces a candidate SQL query with no secrets exposed.

### Milestone 4 — Safety and Guardrails
- Add Guardrails AI, SQLGlot AST checks, schema allowlists, read-only execution, timeout, and row limit.
- **Done when:** unsafe and malformed queries are blocked by tests before database execution.

### Milestone 5 — LangGraph workflow
- Add typed state, nodes, conditional routing, bounded repair loop, execution, analysis, and chart configuration.
- **Done when:** valid questions complete end-to-end and invalid SQL follows the repair/rejection path.

### Milestone 6 — LangSmith
- Add traces, useful metadata, privacy controls, and evaluation dataset/runner.
- **Done when:** a request produces a LangSmith trace when configured, and local operation remains safe if tracing is disabled.

### Milestone 7 — Frontend
- Build question input, examples, answer, SQL panel, results table, chart, validation status, loading and error states.
- **Done when:** a user can submit a question and inspect its SQL, results, insight, and validation outcome.

### Milestone 8 — Quality and deployment
- Add comprehensive tests, Docker Compose, logging, documentation, and UI polish.
- **Done when:** setup works from the README in a clean environment, tests pass, and no critical security issue is known.

### Definition of done
- The app runs locally from documented instructions.
- No placeholder implementation remains in the core path.
- Gemini is used for generation and analysis.
- LangGraph controls the workflow and repair routing.
- Guardrails AI is integrated and invoked, not merely listed as a dependency.
- SQLGlot and database permissions enforce read-only execution.
- LangSmith traces real graph runs when configured.
- The frontend displays real API responses, not hardcoded demo results.
- Tests cover unsafe SQL and graph retry limits.
- No secrets are committed or sent to the browser.
- README explains architecture, setup, testing, tracing, evaluation, and limitations.

---

## 17. Instructions to Antigravity

Treat this document as the authoritative specification.

1. Inspect the existing workspace before creating or overwriting files. Preserve useful existing work.
2. Implement one milestone at a time in the order above.
3. Before coding each milestone, briefly list the files you intend to create or change.
4. Use real supported APIs and verify imports against installed dependency versions. Do not invent functions or pretend integrations work.
5. After each milestone, run relevant tests and fix errors before moving on.
6. Keep the project runnable after each milestone.
7. If a credential is missing, implement the integration and provide clear setup instructions; do not fabricate successful live calls.
8. Do not hardcode fake results, trace links, confidence metrics, or evaluation scores.
9. Do not weaken SQL safety to make a demo pass.
10. If a requirement cannot be implemented as written due to a package/API limitation, explain the limitation and implement the safest compatible alternative.
11. Finish by summarizing implemented features, exact run commands, test results, and any remaining limitations.
12. Prioritize a correct end-to-end vertical slice over superficial breadth.

**First task:** Implement Milestone 1 only. Verify that the FastAPI health endpoint and React frontend run successfully, then report the files created and the commands used to test them. Do not attempt to implement all milestones in one unverified code dump.
