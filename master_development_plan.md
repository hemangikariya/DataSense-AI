# DataSense AI: Software Development Master Plan
## Developer Implementation Guide & Roadmap

---

## 1. Project Folder Initialization

Developers must initialize the repository layout according to the following guidelines:

### Git Repository Setup
1.  Initialize git in the workspace root:
    ```bash
    git init
    git branch -M main
    ```
2.  Create `.gitignore` in the root:
    ```gitignore
    # Python
    __pycache__/
    *.py[cod]
    *$py.class
    .venv/
    venv/
    poetry.lock
    
    # Next.js / Node
    node_modules/
    .next/
    out/
    dist/
    npm-debug.log*
    yarn-error.log*
    
    # Databases & Storage
    local_storage/
    duckdb_temp/
    *.db
    *.parquet
    
    # Environment & Secrets
    .env
    .env.local
    .env.production
    .env.development
    
    # IDEs
    .vscode/
    .idea/
    .DS_Store
    ```

### Repository Structure Shell Commands
Run these commands to set up the directories:
```bash
# Core Folders
mkdir -p backend/src/core backend/src/modules backend/tests/unit backend/tests/integration backend/tests/api backend/tests/ai_eval backend/alembic
mkdir -p frontend/src/app frontend/src/components/ui frontend/src/components/charts frontend/src/components/layouts frontend/src/hooks frontend/src/lib frontend/src/services frontend/src/types frontend/public
mkdir -p infrastructure/docker infrastructure/prometheus infrastructure/grafana
mkdir -p shared/src/types shared/src/utils
```

### Environment Configurations File Layout
Create a `.env.example` in both `backend/` and `frontend/` folders.

#### Backend (`backend/.env.example`):
```ini
# Environment
ENV=development
DEBUG=true

# Security
SECRET_KEY=generate-a-32-byte-hex-string
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Databases
DATABASE_URL=postgresql+asyncpg://postgres:securepass@localhost:5432/datasense
REDIS_URL=redis://localhost:6379/0

# Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadminpass
MINIO_SECURE=false

# LLM Integrations
GEMINI_API_KEY=your-gemini-api-key-here

# Observability
SENTRY_DSN=your-sentry-dsn
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
```

#### Frontend (`frontend/.env.example`):
```ini
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Package Ingestion Pipeline
1.  **Backend Dependencies Setup:** Navigate to `backend/` and initialize Python virtual environments:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    source .venv/bin/activate
    
    pip install --upgrade pip
    pip install fastapi[all] uvicorn sqlalchemy[asyncio] asyncpg alembic celery redis \
                polars pandas pyarrow openpyxl weasyprint sentence-transformers pgvector \
                scikit-learn xgboost prophet shap sqlglot structlog slowapi opentelemetry-api \
                opentelemetry-sdk opentelemetry-instrumentation-fastapi Sentry-sdk pytest pytest-asyncio
    pip freeze > requirements.txt
    ```
2.  **Frontend Dependencies Setup:** Navigate to `frontend/` and initialize the project:
    ```bash
    npm init -y
    npm install next@15 react@19 react-dom@19 typescript @types/react @types/node \
                tailwindcss postcss autoprefixer lucide-react classnames clsx tailwind-merge \
                @tanstack/react-query axios zod react-hook-form @hookform/resolvers \
                echarts plotly.js-dist-min react-grid-layout @types/react-grid-layout
    ```

---

## 2. Development Environment Setup

### Required Runtimes
*   **Python:** Version `3.13+`
*   **NodeJS:** Version `22.x+` (NPM version `10.x+`)
*   **PostgreSQL:** Version `15+` with the `pgvector` extension compiled and enabled.
*   **Redis:** Version `7.0+`
*   **MinIO:** Latest release version (run via local script or Docker image).

### Recommended VS Code Configuration
Create `root/.vscode/settings.json`:
```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": "always",
    "source.fixAll.eslint": "always"
  },
  "python.formatting.provider": "none",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": [
    "backend/tests"
  ],
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "typescript.tsdk": "frontend/node_modules/typescript/lib"
}
```

### Essential Extensions
*   **Ruff (charliermarsh.ruff):** Lints and formats Python code.
*   **ESLint (dbaeumer.vscode-eslint):** Integrates ESLint for JavaScript/TypeScript code.
*   **Prettier (esbenp.prettier-vscode):** Formats TypeScript/React code.
*   **Docker (ms-azuretools.vscode-docker):** Manages container environments.

---

## 3. Project Dependency Graph

The project contains strict execution boundaries. Core system services cannot start development until the underlying infrastructure layers are completed.

```mermaid
graph TD
    %% Phase 1 Foundations
    P1_DB[Postgres + pgvector Initialization] --> P1_Auth[SaaS Multi-Tenant Auth Schema]
    P1_MinIO[MinIO File Storage Setup] --> P1_Auth
    
    %% Phase 2 Datasets
    P1_Auth --> P2_Ingest[Polars Dataset Ingestion Pipeline]
    P2_Ingest --> P2_Clean[Data Quality & Cleaning suggested strategies]
    
    %% Phase 3 Core Analytics
    P2_Clean --> P3_DuckDB[DuckDB Execution Core]
    P3_DuckDB --> P3_Profile[Metadata Profiling & Correlation Engine]
    P3_Profile --> P3_AutoDash[Auto Dashboard Config & Card Generator]
    
    %% Phase 4 AI Integrations
    P3_AutoDash --> P4_Semantic[pgvector Semantic Column Indexing]
    P4_Semantic --> P4_KPI[Hybrid KPI Detection Rules]
    P4_KPI --> P4_ConvBI[Conversational BI AST Query Execution]
    P3_Profile --> P4_Narrative[Gemini Narrative Summary Engine]
    
    %% Phase 5 Predictions & Reports
    P3_DuckDB --> P5_XGBoost[XGBoost & Prophet Training Routines]
    P5_XGBoost --> P5_SHAP[SHAP Feature Explanations]
    P4_Narrative & P3_AutoDash --> P5_Report[WeasyPrint PDF, Excel, CSV Export]
    
    %% Phase 6 Infrastructure Hardening
    P5_SHAP & P5_Report --> P6_Audit[Audit Logging & Compliance Retentions]
    P6_Audit --> P6_Flag[Feature Flag Evaluation Middleware]
    P6_Flag --> P6_OTel[OTel Observability & Prometheus Monitoring]
```

### Critical Path Elements
1.  **Multi-Tenant Database Migrations:** Essential for database mappings and authentication.
2.  **Polars Processing Framework:** Standardizes dataset structures, creating the Parquet files used by DuckDB.
3.  **DuckDB Core Sandbox Setup:** Processes all analytical calculations, Auto Dashboards, and Conversational BI requests.
4.  **pgvector Indexes:** Essential to mapping conversational questions to schemas.

---

## 4. Master Development Sequence

```
[Phase 1: Foundation]
├── Database migration sets for Tenants (Orgs, Workspaces, Members, Users).
└── JWT authentication context with subdomain configurations.

[Phase 2: Ingestion & Verification]
├── Polars processing routines to ingest, validate, and clean datasets.
└── MinIO storage routes configured with Organization / Workspace keys.

[Phase 3: Analytics & Visualization]
├── Thread-safe DuckDB analytical database pools.
└── Automated Dashboard layout builder using React-Grid-Layout.

[Phase 4: Semantic Search & AI]
├── pgvector schema indexing and Hybrid KPI identification logic.
└── Conversational SQL generation and AST-based SQL query verification.

[Phase 5: Predictions & Reporting]
├── XGBoost classification and Prophet forecasting models.
├── SHAP value calculations and visual impact explanations.
└── WeasyPrint report engine generating PDF, Excel, and CSV files.

[Phase 6: Infrastructure & Compliance]
├── Multi-tenant Feature Flag engine.
├── Partitioned Audit Log database tables.
└── Prometheus metrics and Sentry error logs.
```

---

## 5. Sprint Planning

### Sprint 1: Foundation, Multi-Tenant Authentication & Storage
*   **Goal:** Establish SaaS workspace databases, multi-tenant Auth, and the storage layer.
*   **Deliverables:**
    *   DDL migration scripts for `organizations`, `workspaces`, `users`, and `workspace_members`.
    *   FastAPI JWT authentication middleware containing tenant metadata claims.
    *   MinIO S3 Client utility class configured with tenant path namespaces.
*   **Estimated Effort:** 80 Hours.
*   **Dependencies:** None.
*   **Acceptance Criteria:**
    *   Auth requests block users from accessing workspaces they do not belong to.
    *   Files are successfully uploaded and written to isolated tenant folders in MinIO.

### Sprint 2: Data Ingestion, Validation & Cleaning Engine
*   **Goal:** Build Polars processing pipelines to validate and clean datasets.
*   **Deliverables:**
    *   Polars-based file layout parser mapping CSV, Excel, and JSON data.
    *   Data Quality Score calculation formula engine (scoring Completeness, Timeliness, etc.).
    *   Cleaning strategy handlers (imputing missing values, removing outliers, casting data types).
*   **Estimated Effort:** 80 Hours.
*   **Dependencies:** Sprint 1.
*   **Acceptance Criteria:**
    *   Uploaded files are validated, processed, and written to storage as optimized Parquet files.
    *   Dynamic quality scores and suggested cleanups return matching JSON structures.

### Sprint 3: DuckDB Engine, Profiling & Auto Dashboards
*   **Goal:** Implement DuckDB analytical queries and auto-generate dashboard layouts.
*   **Deliverables:**
    *   DuckDB thread-safe pool manager executing queries over workspace Parquet files.
    *   Auto-profiling scripts for summary stats, category groupings, and Pearson correlations.
    *   Heuristics-based dashboard configuration builder and React-Grid-Layout frontend components.
*   **Estimated Effort:** 80 Hours.
*   **Dependencies:** Sprint 2.
*   **Acceptance Criteria:**
    *   DuckDB processes files up to 500MB, executing typical aggregates in `<1.2 seconds`.
    *   Dynamic dashboards are successfully saved and rendered on the Next.js grid.

### Sprint 4: Conversational BI, pgvector & Gemini Integration
*   **Goal:** Build the natural language Conversational BI query pipeline.
*   **Deliverables:**
    *   pgvector cosine matching service to retrieve relevant database columns.
    *   sqlglot AST SQL parsing guardrails to prevent command injections.
    *   Gemini API prompt builder and fallback mechanisms.
*   **Estimated Effort:** 80 Hours.
*   **Dependencies:** Sprint 3.
*   **Acceptance Criteria:**
    *   User questions are translated to SQL, validated, and executed against DuckDB.
    *   Unsafe SQL queries (e.g. commands containing drop / update statement nodes) are immediately blocked.

### Sprint 5: ML Predictions, Explainability (SHAP) & Reporting
*   **Goal:** Implement predictive models, SHAP explanations, and document exporting.
*   **Deliverables:**
    *   Prophet (time-series forecast) and XGBoost (churn classification) training routines.
    *   SHAP calculation engine generating global feature importance values.
    *   WeasyPrint PDF, formatted Excel, and zipped CSV export workers.
*   **Estimated Effort:** 80 Hours.
*   **Dependencies:** Sprint 3.
*   **Acceptance Criteria:**
    *   Model runs generate evaluation metrics and SHAP force-plot coordinates.
    *   PDF reports compile and render charts correctly.

### Sprint 6: Observability, Feature Flags & Hardening
*   **Goal:** Implement feature flags, audit logging, system monitoring, and production deployment configuration.
*   **Deliverables:**
    *   Dynamic Feature Flag service checking overrides per user, org, and environment.
    *   Monthly partitioned `audit_logs` database tables with automated triggers.
    *   Prometheus metrics, OTel collectors, Sentry tracing setup, and Docker Compose configurations.
*   **Estimated Effort:** 80 Hours.
*   **Dependencies:** Sprint 4 & Sprint 5.
*   **Acceptance Criteria:**
    *   Audit logs are written asynchronously after each system action.
    *   API response metrics and trace spans are collected by the OTel exporter.

---

## 6. Backend Implementation Plan

```
[Auth & Tenants] ──► [MinIO Client] ──► [Polars Ingest] ──► [DuckDB Sandbox] ──► [AI / ML & SHAP] ──► [Audit & Flags]
```

### Detailed Sequence
1.  **Auth & Tenants:** Build user registration, Google login, and subdomain tenant parsing. Enforcing tenant check middleware first guarantees that all downstream modules are secured by design.
2.  **MinIO Client:** Develop file upload paths to keep tenant datasets isolated at rest.
3.  **Polars Ingestion:** Parse raw files into standardized Parquet file partitions.
4.  **DuckDB Pool Manager:** Initialize read-only DuckDB analytical databases on backend workers.
5.  **AI & ML Service:** Integrate the Gemini API prompt flows and XGBoost/SHAP model structures.
6.  **Audit & Flags:** Implement audit logging and feature flags dynamically to ensure security and compliance before starting production testing.

---

## 7. Frontend Implementation Plan

1.  **Authentication & Tenant Views (`(auth)/` & `settings/`):** Set up forms for login, signup, organization settings, and workspace routing.
2.  **Workspace Navigation Layout:** Create shared navigation trees, sidebars, and theme state providers.
3.  **Dataset Upload & Cleaner View:** Build progress bars, metadata tables, and dashboard controls to apply cleaning rules.
4.  **Analytics Grid Dashboard:** Render the interactive drag-and-drop dashboard using ECharts widgets.
5.  **Conversational BI Console:** Build chat input boxes, markdown bubble components, and SQL toggle displays.
6.  **Predictions & Models Wizards:** Set up parameters select panels, model validation plots, and SHAP visualizers.

---

## 8. Database Migration & Versioning Strategy

### Database Versioning & Schema Control
All PostgreSQL schemas are versioned and managed using **Alembic**.

### Migration Commandments
*   **Zero-Downtime Rule:** Write migrations that are backward compatible. Do not drop tables or columns immediately; instead, deprecate and drop them in the next release cycle.
*   **Safe Indexes Creation:** All indexes on production tables must use the `CONCURRENTLY` modifier to prevent database locking:
    ```sql
    CREATE INDEX CONCURRENTLY idx_datasets_tenant_isolation ON datasets(organization_id, workspace_id);
    ```

### Migration Execution Plan
*   **Local Setup:** Run database migrations locally using uvicorn bootstrap:
    ```bash
    alembic revision --autogenerate -m "add_saas_tenancy"
    alembic upgrade head
    ```
*   **Rollback Strategy:** Every migration script must include a valid `downgrade()` function to support instant rollbacks:
    ```python
    def downgrade():
        op.drop_index('idx_datasets_tenant_isolation')
        op.drop_table('datasets')
    ```

---

## 9. API Development Roadmap

FastAPI routing files must be implemented in the following order to ensure a logical testing path:

### 1. Verification APIs
*   `GET /health` $\rightarrow$ System health monitoring endpoint.
*   `POST /api/v1/auth/signup` $\rightarrow$ Core registration interface.
*   `POST /api/v1/auth/login` $\rightarrow$ Retrieval of active JWT claims.

### 2. Dataset Ingest & Clean APIs
*   `POST /api/v1/datasets/upload` $\rightarrow$ Start parsing files into Parquet formats.
*   `GET /api/v1/datasets/{id}/metadata` $\rightarrow$ Retrieve column definitions and quality scores.
*   `POST /api/v1/datasets/{id}/clean` $\rightarrow$ Apply data cleaning adjustments.

### 3. Analytics & Dashboard APIs
*   `POST /api/v1/dashboards/auto-generate` $\rightarrow$ Generate dynamic dashboard configurations.
*   `GET /api/v1/analytics/health-score` $\rightarrow$ Get computed Business Health Scores.

### 4. Advanced AI APIs
*   `POST /api/v1/conversations/chat` $\rightarrow$ Submit natural language queries.
*   `POST /api/v1/predictions/train` $\rightarrow$ Train models and compute SHAP values.
*   `POST /api/v1/reports/export` $\rightarrow$ Export formatted reports.

---

## 10. AI Development Roadmap

AI modules must be built in this order to match the data dependencies of the pipeline:

```mermaid
flowchart LR
    A[Dense Embeddings] --> B[pgvector Indexing]
    B --> C[Hybrid KPI Discovery]
    C --> D[Conversational SQL Gen]
    D --> E[Gemini Narrative Summary]
    E --> F[Explainable SHAP Feature Impact]
```

### Rationale
*   Column names and descriptions must be converted to vector format before pgvector can run semantic schema lookups.
*   Matched columns are required for the KPI logic to identify business metrics.
*   KPI classifications and schemas are required to formulate conversational SQL prompts.
*   Model features must be defined before running SHAP explanations.

---

## 11. Testing Execution Plan

```
Feature Branch Coding
  ├── Unit Tests (Run on local commit hook)
  └── Integration Tests (Run on pull request target)
        └── API Endpoint Tests (Executed in CI test stage)
              └── AI Evaluations (Run before release stage)
```

*   **Unit Tests:** Written during development of core modules. Code coverage must meet a minimum target of `85%`.
*   **Integration Tests:** Validates correct communication between modules, database connections, and file uploads.
*   **API Tests:** Uses FastAPI's `TestClient` to test all authentication header operations and mock database inputs.
*   **AI evaluations:** Tests prompt security and sqlglot sanitization rules against deliberate prompt injections.
*   **Load & Performance Tests:** Simulated user traffic runs before final release checks to audit concurrent uploads and database locks.

---

## 12. Git Workflow & Release Strategy

### Git Branching Model
DataSense AI implements the **GitFlow** branching strategy.

```
main        [Production Release Version tag v1.0.0]
  ▲
release/    [Release prep & validation tests]
  ▲
develop     [Central Integration Branch]
  ▲
feature/    [Feature implementation branches]
```

### Commit Naming Convention
Commit messages must follow the **Conventional Commits** format:
```
<type>(<scope>): <short summary description>

[Optional body explaining rationale]
```
*   `feat(auth)`: Add JWT claims for workspace context.
*   `fix(duckdb)`: Clean up thread connection allocations.
*   `test(evals)`: Add prompt injection security tests.

### Branch Review and Merging Guidelines
*   **PR Mandate:** Feature branches require at least 2 approvals from the engineering team before merging to `develop`.
*   **CI Validation:** Automated pipeline checks must pass (linting, tests, security audits) before the pull request can be merged.
*   **Merge Type:** Enforce Squash and Merge to keep a clean history.

---

## 13. Coding Standards & Conventions

### Python Standards
*   **Linter & Formatter:** **Ruff** is used to enforce formatting rules and PEP 8 guidelines.
*   **Type Hinting:** Strictly type all function arguments and return values:
    ```python
    async def get_dataset_metadata(dataset_id: UUID) -> DatasetMetadataResponse:
    ```

### TypeScript & React Standards
*   **Framework Rules:** Next.js pages must utilize strict TypeScript typing.
*   **Hooks Pattern:** Keep component files focused on layout and export visual changes to dedicated hook files.

### Naming Conventions
*   **Variables, Functions, Files:** Python uses `snake_case`, TypeScript uses `camelCase`, and React components use `PascalCase`.
*   **Database Objects:** Tables, columns, and indexes must use `snake_case`. Table names must be plural (e.g. `users`, `datasets`).
*   **API Routes:** Endpoint paths must use lowercase kebab-case (e.g. `/api/v1/feature-flags`).

---

## 14. Definition of Done (DoD)

### For a Feature
*   All function signatures are typed, and core logic is verified with unit tests.
*   No styling issues or console warnings exist in the frontend component files.

### For an API Endpoint
*   Zod validation schemas are enforced on all request payloads.
*   The endpoint returns standardized error codes for invalid inputs.
*   All API routes are documented using OpenAPI/Swagger annotations.

### For an AI Module
*   The sqlglot parser validates that all database operations are restricted to SELECT statements.
*   Prompt templates are protected against basic injection attacks.

### For a Release
*   Database migration scripts are verified with rollback procedures.
*   All Grafana dashboards and Prometheus alerts are configured and verified.

---

## 15. Code Review Checklist

### 1. Security Compliance
*   Are inputs sanitized on both the frontend and backend?
*   Do analytical routes validate organization and workspace ownership claims?
*   Are credentials and key variables managed using environment configurations?

### 2. Code Quality & Performance
*   Does the code avoid loading large files entirely into memory?
*   Are SQLAlchemy queries structured to prevent N+1 database connection lookups?
*   Are Redis cache namespaces invalidated correctly when data changes?

### 3. Verification Coverage
*   Do the unit test suites cover standard success paths and edge cases?
*   Are API test assertions verifying status codes and error payloads?

---

## 16. Technical Risk Mitigation Matrix

| Potential Risk | Impact | Mitigation Strategy | Emergency Recovery Plan |
| :--- | :--- | :--- | :--- |
| **Cross-Tenant Data Leakage** | Critical | Enforce tenant check filters on all database queries. | Revoke active user tokens, isolate database instances, and analyze access logs. |
| **DuckDB Memory Exhaustion**| High | Process incoming files in small chunks using Polars. | Restart backend worker processes and scale server resources dynamically. |
| **Gemini API Outage** | Medium | Cache common query outputs and use structured JSON templates. | Fall back to standard search filters and display a system notice to the user. |
| **Prompt Injection Attack** | High | Filter input queries against blacklisted injection patterns. | Flag the user's IP, log the incident, and alert security administrators. |

---

## 17. Infrastructure Deployment Checklist

Verify these configurations before executing deployment steps:

*   [ ] **Env variables:** Ensure production credentials and keys are configured in the environment.
*   [ ] **Migrations:** Check that database tables are up-to-date:
    ```bash
    alembic current
    ```
*   [ ] **Redis Cache:** Verify that Redis is running and reachable by backend workers.
*   [ ] **MinIO Storage:** Test that the system has read/write permissions for bucket folders.
*   [ ] **Nginx Routing:** Confirm Nginx is configured to terminate SSL and route subdomains correctly:
    ```bash
    nginx -t
    ```
*   [ ] **Observability:** Verify Prometheus is collecting system metrics and Sentry is capturing error logs.

---

## 18. Production Release Checklist

Run these validation steps on the staging server before modifying DNS settings:

```
[Deploy Migrations] ──► [Verify Storage] ──► [Test Rate Limits] ──► [Run Smoke Tests] ──► [Go Live]
```

### Pre-Flight Verification List
*   [ ] Run the test suite on the staging server:
    ```bash
    pytest tests/api/
    ```
*   [ ] Verify rate limiting is working by running automated stress tests.
*   [ ] Confirm PII masking is working by querying fields containing simulated sensitive data.
*   [ ] Confirm the backup cron job is running and writing database dumps to MinIO.

---

## 19. Post-Deployment Monitoring

Execute these health checks immediately after deployment is complete:

1.  **Monitor Health Endpoint:** Verify `/health` returns a `200 OK` status.
2.  **Verify Observability Metrics:** Confirm Prometheus is collecting API response metrics.
3.  **Trace Application Logs:** Check Grafana Loki to confirm there are no database connection errors or exceptions.
4.  **Execute Smoke Tests:** Log in, select a workspace, upload a sample dataset, and verify the dashboard renders correctly.

---

## 20. Developer Guidelines & Anti-Patterns

### Anti-Patterns to Avoid
*   **Do Not Query Without Tenant Filters:** Never query database tables without filtering by `organization_id` or `workspace_id`.
*   **Do Not Use Raw Pandas on Ingest:** Never load uploaded raw files directly into memory using Pandas; always use Polars for validation, cleaning, and parquet conversion.
*   **Do Not Connect directly to DuckDB:** Never bypass the sandboxed connection manager to execute raw SQL queries.

### Performance & Security Best Practices
*   **Use Connection Pools:** Always execute SQL queries using SQLAlchemy connection pools.
*   **Mask PII Columns:** Always verify PII flags on columns and mask values before returning query responses.
*   **Invalidate Caches:** Always invalidate Redis cache namespaces immediately when datasets or dashboard configurations are updated.
