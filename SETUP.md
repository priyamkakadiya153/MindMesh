# MindMesh Setup & Launch Guide

Before executing the frontend and backend servers, follow this guide to initialize environment variables, configure the relational database schema, and spin up cache systems.

---

## 1. Setup Environment Variables

First, copy the example environment configuration into the active environments.

### Root Directory
Copy `.env.example` in the root workspace folder to `.env`:
```powershell
cp .env.example .env
```

### Backend Configuration
Create an `.env` file under `apps/api/` matching your postgres, redis, and Google Gemini API credentials:
```env
PORT=4000
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/mindmesh"
REDIS_URL="redis://localhost:6379"
JWT_SECRET="mindmesh_super_secret_jwt_key_123!"
JWT_REFRESH_SECRET="mindmesh_refresh_token_secret_key_456!"
NODE_ENV=development
GEMINI_API_KEY="your-google-gemini-api-key-here"
```

---

## 2. Start PostgreSQL (with pgvector) & Redis

MindMesh requires PostgreSQL (with the `pgvector` extension enabled) and Redis.

### Using Docker (Recommended)
If you have Docker Desktop installed, spin up both databases from the root directory:
```powershell
docker compose up -d
```

### Manual Installation
If running databases natively on Windows:
* Ensure PostgreSQL 16+ is running on port `5432` with a database named `mindmesh`.
* Ensure pgvector extension is installed.
* Ensure Redis server is active on port `6379`.

---

## 3. Run Database Migrations (Backend)

Run Alembic schema upgrades to generate all required tables and indices:
```powershell
# From apps/api/ directory
cd apps/api
..\..\.venv\Scripts\alembic upgrade head
```

---

## 4. Run Development Servers

### Start Backend (Python FastAPI)
From the root workspace directory, change directory and launch uvicorn:
```powershell
cd apps/api
..\..\.venv\Scripts\python -m uvicorn main:app --reload --port 4000
```

### Start Frontend (TypeScript React)
From the root workspace directory, launch Vite:
```powershell
npm run dev:web
```

---

## 5. Verify Health

Check if all systems are alive by executing:
```powershell
# API Health Endpoint
curl http://127.0.0.1:4000/api/v1/monitoring/health

# CLI Sanity Check Tool
cd apps/api
..\..\.venv\Scripts\python -m app.production_verify
```
