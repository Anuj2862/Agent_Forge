# Member 4 Setup Guide — Evolution Memory & Frontend

This document outlines how to set up and run the Agent Forge system using Member 4's implementation of the Evolution Memory Store, API, and Next.js Frontend.

## Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional, for PostgreSQL/Redis)

## Local Development Setup

### 1. Backend API & Database

The backend API uses an async SQLAlchemy architecture. By default, it uses a local SQLite database (`agentforge_memory.db`) so you can run the system immediately without Docker.

```bash
# Set up Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the FastAPI server (auto-creates SQLite tables on startup)
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. Swagger UI at `/docs`.

### 2. Next.js Frontend Dashboard

```bash
# Navigate to the frontend directory
cd frontend

# Install dependencies
npm install

# Run the development server
npm run dev
```

The frontend dashboard will be available at `http://localhost:3000`.

## Production / Full Stack Setup (Docker)

To run the complete system with a real PostgreSQL database, use Docker Compose:

```bash
docker-compose up -d
```

This will spin up:
- PostgreSQL (port 5432)
- Redis (port 6379)
- FastAPI Backend (port 8000)
- Next.js Frontend (port 3000)

## Simulation Layer Note

> [!NOTE]
> Since Members 1 and 2 are still working on their branches (`member-1`, `member-2`), their implementations of `MetaController` and `ExecutionEngine` are stubs. 
> To ensure the E2E Mid-Sem Demo works fully, the API routes (`task_routes.py`, `execution_routes.py`, etc.) are temporarily wired to `app.api.simulate`. 
> These simulators generate realistic outputs based on templates and randomized timing so you can test the frontend and memory persistence pipeline without blockers.

## Testing

Run the integration test suite to verify the memory store, retriever, and API routes:

```bash
pytest tests/ -v
```
