# AI Habitat — Development Guide

## Prerequisites

- Python ≥ 3.12 (tested with 3.14.7)
- Node.js ≥ 20 (tested with 26.8.1)
- npm ≥ 10 (tested with 11.19.0)
- Docker (optional — for PostgreSQL; not required for local dev)

## Local Development (without Docker)

### 1. Environment Configuration

```bash
cd ai-habitat
cp .env.example .env
```

Default `.env` uses SQLite — no additional database setup needed.

### 2. Backend

```bash
cd apps/api

# Install dependencies (including dev/test dependencies)
pip install -e ".[dev]"

# Run the API server with auto-reload
uvicorn app.main:app --reload --port 8000
```

API will be available at:
- http://localhost:8000 — API root
- http://localhost:8000/docs — Swagger UI
- http://localhost:8000/redoc — ReDoc
- http://localhost:8000/health — Liveness check
- http://localhost:8000/api/v1/health — Application health
- http://localhost:8000/api/v1/version — Version info

### 3. Frontend

```bash
cd apps/web

# Install dependencies
npm install

# Run dev server with hot reload
npm run dev
```

Frontend will be available at http://localhost:5173.

### 4. Running Both Together (PowerShell)

```powershell
.\scripts\dev.ps1
```

This starts both backend and frontend in parallel.

## Running Tests

### Backend

```bash
cd apps/api
pytest -v
```

### Frontend

```bash
cd apps/web
npm run build    # TypeScript type-check + build
```

## Database

### SQLite (default for local dev)

No setup required. A file `ai_habitat.db` is created automatically in `apps/api/`.

### PostgreSQL (Docker)

When Docker is available:

```bash
docker compose up db -d
```

Then update `.env`:

```
DATABASE_URL=postgresql+asyncpg://habitat:habitat@localhost:5432/ai_habitat
```

### Migrations

```bash
cd apps/api

# Generate a new migration after model changes
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head
```

## Structured Logging

All API logs are structured JSON:

```json
{
  "timestamp": "2024-01-01T00:00:00+00:00",
  "level": "INFO",
  "logger": "ai_habitat",
  "message": "request_completed",
  "request_id": "abc-123",
  "method": "GET",
  "path": "/api/v1/health",
  "status": 200,
  "duration_ms": 4.2
}
```

Every request includes an `X-Request-ID` header for tracing.
