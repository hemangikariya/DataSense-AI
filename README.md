# DataSense AI - AI-Powered Business Intelligence Platform
## Phase 1: Project Setup & Foundation Guide

This repository contains the initialization structures for DataSense AI. Phase 1 delivers a dockerized Modular Monolith backend powered by FastAPI, and a Next.js 15 frontend template configured with strict TypeScript, styling inputs, API clients, and telemetry setups.

---

## Prerequisites
Ensure the following development environments are available on the local host machine:
*   **Python:** Version `3.13+`
*   **NodeJS:** Version `22.x+` (NPM version `10.x+`)
*   **Docker & Docker Compose:** Latest stable release versions.

---

## 1. Quick Start with Docker
The platform can be orchestrated inside a local Docker network.

### Boot containers:
From the root workspace directory, run:
```bash
docker-compose up --build
```
This builds and starts the following services:
1.  **datasense_nginx (Port 80):** Reverse Proxy Gateway routing `/` to NextJS and `/api/` to FastAPI.
2.  **datasense_frontend (Port 3000):** Next.js 15 UI template.
3.  **datasense_backend (Port 8000):** FastAPI ASGI application backend.
4.  **datasense_db (Port 5432):** PostgreSQL database with `pgvector` enabled.
5.  **datasense_redis (Port 6379):** Broker & Cache server.
6.  **datasense_minio (Ports 9000/9001):** Object storage server & admin console.

### Database Migrations:
Once the PostgreSQL container is active, execute Alembic migrations:
```bash
docker-compose exec backend alembic upgrade head
```

---

## 2. Local Host Development Setup

If running backend and frontend services natively on the host system:

### A. Backend Setup
1.  Navigate to the `backend/` directory:
    ```bash
    cd backend
    ```
2.  Initialize and activate a virtual environment:
    ```bash
    python -m venv .venv
    # Windows:
    .venv\Scripts\activate
    # macOS/Linux:
    source .venv/bin/activate
    ```
3.  Install python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Launch local development server:
    ```bash
    uvicorn src.app:app --reload --host 127.0.0.1 --port 8000
    ```

### B. Frontend Setup
1.  Navigate to the `frontend/` directory:
    ```bash
    cd ../frontend
    ```
2.  Install npm packages:
    ```bash
    npm install
    ```
3.  Start Next.js dev server:
    ```bash
    npm run dev
    ```

---

## 3. Database Migrations Guide

Local Alembic migration operations:
*   **Generate revision:**
    ```bash
    alembic revision --autogenerate -m "description_of_change"
    ```
*   **Execute upgrade:**
    ```bash
    alembic upgrade head
    ```
*   **Roll back migration:**
    ```bash
    alembic downgrade -1
    ```

---

## 4. Testing & Code Quality

Verify Phase 1 configurations using the test suite.

### Run Tests:
Navigate to the `backend/` directory and run:
```bash
pytest
```

### Ruff Formatting & Lint checks:
```bash
ruff check .
ruff format .
```

---

## 5. Troubleshooting & Health Checks

### Check System Status:
Query the health check endpoint to inspect infrastructure connectivity (Postgres, Redis, MinIO):
```bash
curl http://localhost/health
```
**Expected successful output response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-07-13T22:10:00Z",
  "services": {
    "backend": "healthy",
    "postgres": "healthy",
    "redis": "healthy",
    "minio": "healthy"
  }
}
```
