# AI Habitat — Architecture

## Overview

AI Habitat is a persistent digital environment for human–AI collaboration. The v0.1 architecture implements a clean modular monolith: one human, one AI, one persistent workspace.

## System Architecture

```
Frontend (React/TS)
       │
       │  HTTP REST
       ▼
Backend (FastAPI)
       │
       │  SQLAlchemy (async)
       ▼
Database
       │
  ┌────┴────┐
  │ SQLite  │  ← local development
  │ (dev)   │
  ├─────────┤
  │ Postgres│  ← production / Docker
  │ (prod)  │
  └─────────┘
```

## Invariants

1. **Frontend → HTTP API → Backend → SQLAlchemy → Database** — no shortcuts.
2. **Domain code never knows which database engine is running.** All access goes through SQLAlchemy.
3. **Frontend never talks directly to:** Database, AI Provider, filesystem.
4. **Every API response** uses the `{success, data, error, meta}` envelope.
5. **Every request** carries an `X-Request-ID` for observability tracing.

## Backend Layers

```
API Route Handlers
       │
Service Layer (business logic)      ← future phases
       │
Repository Layer (data access)      ← future phases
       │
SQLAlchemy ORM / Async Session
       │
Database Engine
```

AI access flows through:

```
AI Service → AIProvider abstraction  ← future phases
```

Capability execution flows through:

```
Capability Service → Permission Service → Executor  ← future phases
```

## Monorepo Structure

```
ai-habitat/
├── apps/
│   ├── api/          # Python — FastAPI backend
│   │   ├── app/
│   │   │   ├── api/      # Route handlers
│   │   │   ├── core/     # Config, DB, errors, middleware, logging
│   │   │   ├── models/   # SQLAlchemy ORM models
│   │   │   ├── schemas/  # Pydantic request/response schemas (Phase 2+)
│   │   │   ├── services/ # Business logic (Phase 2+)
│   │   │   └── repositories/  # Data access (Phase 2+)
│   │   ├── alembic/      # Database migrations
│   │   └── tests/
│   └── web/          # TypeScript — React + Vite frontend
│       └── src/
├── infra/docker/     # Dockerfiles
├── docs/             # Documentation
├── scripts/          # Development scripts
└── docker-compose.yml
```

## Technology Stack

| Layer       | Technology              |
|-------------|------------------------|
| Frontend    | React, TypeScript, Vite, Tailwind CSS |
| Backend     | Python 3.14, FastAPI, Pydantic |
| ORM         | SQLAlchemy 2.x (async) |
| Migrations  | Alembic               |
| Database    | SQLite (dev) / PostgreSQL (prod) |
| Testing     | pytest, pytest-asyncio, httpx |

## Configuration

All configuration flows through `pydantic-settings` → environment variables / `.env` file. See `.env.example` for available settings.

## Phase 1 Endpoints

| Endpoint            | Purpose                          |
|---------------------|----------------------------------|
| `GET /health`       | Infrastructure/liveness probe    |
| `GET /api/v1/health`| Application health check         |
| `GET /api/v1/version`| Version and environment info    |
