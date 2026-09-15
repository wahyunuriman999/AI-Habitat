# AI Habitat v0.1

A persistent digital environment where a human and an AI can work together over time through identity, memory, workspace, capabilities, permissions, and observable history.

## Quick Start (Local Development)

### Prerequisites

- Python ≥ 3.12
- Node.js ≥ 20
- npm ≥ 10

### Backend

```bash
cd apps/api
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd apps/web
npm install
npm run dev
```

### Endpoints

| Service     | URL                          |
|-------------|------------------------------|
| Frontend    | http://localhost:5173         |
| API         | http://localhost:8000         |
| API docs    | http://localhost:8000/docs    |
| Liveness    | http://localhost:8000/health  |
| API health  | http://localhost:8000/api/v1/health |
| Version     | http://localhost:8000/api/v1/version |

### Environment

Copy `.env.example` to `.env` and adjust values:

```bash
cp .env.example .env
```

Default configuration uses SQLite for local development (no Docker required).

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Project Structure

```
ai-habitat/
├── apps/
│   ├── api/            # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/    # Route handlers
│   │   │   ├── core/   # Config, DB, errors, middleware, logging
│   │   │   └── models/ # SQLAlchemy ORM models
│   │   ├── alembic/    # Database migrations
│   │   └── tests/
│   └── web/            # React + TypeScript frontend
├── infra/docker/       # Dockerfiles (future use)
├── docs/               # Documentation
├── scripts/            # Development scripts
└── docker-compose.yml  # Docker Compose (future use)
```

## Testing

```bash
cd apps/api
pytest -v
```

## License

Proprietary — All rights reserved.
