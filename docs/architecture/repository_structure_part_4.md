# Repository Structure (Part 4 — Backend Repository Structure)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official backend repository structure for MindMesh. The backend follows a **Feature-First Modular Clean Architecture** where each business domain is self-contained while sharing common infrastructure.

---

## Backend Philosophy
The backend is responsible for:
* Business Logic
* Authentication & Authorization
* Database Operations
* AI Coordination
* File Management
* Search
* WebSockets
* Background Processing
* API Documentation

The backend must **never** contain UI logic, presentation code, styling, or frontend components.

---

## Technology Stack
* **Language**: Python 3.12+
* **Framework**: FastAPI (Pydantic v2)
* **Database**: PostgreSQL (SQLAlchemy 2.x, Alembic, psycopg2/pg8000)
* **Real-time**: WebSockets (native ASGI websockets / Socket.io)
* **AI/RAG**: LangChain, Sentence Transformers, ChromaDB / pgvector
* **Queue / Broker**: Redis

---

## Official Folder Structure

```text
apps/api/
├── app/
│   ├── core/               # Security, authentication helpers, logging, error handling
│   ├── domains/            # Feature-first domain modules
│   │     ├── authentication/
│   │     ├── users/
│   │     ├── conversations/
│   │     ├── messages/
│   │     ├── files/
│   │     ├── knowledge/
│   │     ├── search/
│   │     ├── notifications/
│   │     ├── dashboard/
│   │     ├── settings/
│   │     └── administration/
│   ├── shared/             # Reusable core components (BaseRepository, BaseService, ResponseModels)
│   ├── ai/                 # AI & Retrieval layer (chunking, retrievers, extraction pipelines)
│   ├── api/                # Versioned HTTP API controllers (v1/, v2/)
│   ├── middleware/         # HTTP middleware (CORS, Rate Limiting, Logging)
│   ├── websocket/          # Real-time WebSocket connection managers and room broadcasts
│   ├── workers/            # Asynchronous task workers (embedding generation, summarization)
│   ├── database/           # Engine setup, session pooling, and migrations
│   ├── storage/            # File storage providers (Local, MinIO, AWS S3)
│   ├── config/             # Environment setup loader
│   ├── utils/              # Pure utility functions split by responsibility
│   │
│   ├── main.py             # FastAPI App instance and configuration
│   └── lifespan.py         # App startup and shutdown listeners
├── tests/                  # Unit and integration test suites
├── alembic/                # Alembic database migration scripts
├── pyproject.toml          # Build system requirements
├── requirements.txt        # Backend dependencies
├── Dockerfile              # Docker container deployment configuration
└── .env.example            # Backend env template
```

---

## Domain Architecture Layout
Every domain directory inside `domains/` must be self-contained:
```text
domains/<name>/
├── api/             # HTTP route controllers
├── services/        # Business logic services
├── repositories/    # Database queries and persistence CRUD operations
├── models/          # Relational entities (SQLModel classes)
├── schemas/         # Request & Response Pydantic DTO validation models
├── validators/      # Custom domain logic validation
├── dependencies/    # FastAPI dependency injections
├── events/          # Asynchronous publish/subscribe event hooks
├── exceptions/      # Domain specific custom exceptions
└── constants/       # Domain-wide settings and limits
```

---

## Core Backend Rules

### 1. Dependency Rule
Dependency flow must strictly proceed in the following direction:
```text
API Controllers (app/api/v1) -> Services (domains/) -> Repositories (domains/) -> Database (app/database)
```
* Services coordinate the logic, call database repositories, and call AI pipelines.
* Repositories must never perform business logic, call external APIs, or execute AI functions.
* Circular dependencies across modules are prohibited.

### 2. Service and Repository isolation
* No direct database queries are allowed inside API routers (must go through the service layer).
* Database ORM models should not be returned directly through API endpoints (use Pydantic Schema DTOs for requests and responses).

### 3. Asynchronous Offloading
* Heavy operations (e.g., file metadata extraction, embedding generation, text summarization) must be executed in background queues (`app/workers/`) to prevent blocking main REST/WebSocket loops.
