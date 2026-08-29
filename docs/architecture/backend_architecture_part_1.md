# Backend Architecture (Part 1 — Backend Design Principles & Clean Architecture)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official backend architecture for MindMesh. It establishes the engineering principles, architectural patterns, module boundaries, request lifecycle, and backend development standards that every feature must follow.

---

## Backend Philosophy
The backend is responsible for transforming business requirements into reliable, secure, scalable, and maintainable services. The backend represents the business domain of MindMesh, managing authentication, domain workflows, persistence, background queues, AI coordination, and WebSocket notifications.

---

## Clean Architecture Layers
MindMesh implements a strict layered Clean Architecture:

```text
HTTP Request -> API/Controller -> Dependency Injection -> Services -> Repositories -> Database
```

### 1. API Layer (`app/api/`)
* **Responsibilities**: REST routes, request payload schemas, user authentication parsing, authorization guards, and CORS.
* *Constraint*: Router modules must remain thin. Business logic or database calls are prohibited inside routers.

### 2. Service Layer (`domains/<name>/services/`)
* **Responsibilities**: Core business rules, transactions, AI coordination, event dispatching, and workflow management.
* *Constraint*: All business logic belongs to this layer. Services do not expose raw database tables or connection configurations.

### 3. Repository Layer (`domains/<name>/repositories/`)
* **Responsibilities**: CRUD operations, filtering, database queries, and transaction persistence.
* *Constraint*: Repositories communicate exclusively with the database. They must not perform business rules, make external API queries, or call AI services.

### 4. AI Layer (`app/ai/`)
* **Responsibilities**: Chunks extraction, embedding indexes, semantic search queries, and prompt compilation.
* *Constraint*: Accessible only via the Service layer.

### 5. Infrastructure Layer (`app/database/`, `app/storage/`)
* **Responsibilities**: Session managers, local disks, external storage systems, and cache instances.

---

## Centralized Configurations & Exception Controls
* **Pydantic Validation**: Request payloads are parsed and validated via Pydantic Schemas before reaching the Service layer.
* **Centralized Exceptions**: Global middleware catches database errors, validation failures, or authentication timeouts, mapping them to standard JSON formats.
* **Environment Variables**: No hardcoded secrets. Database connections, Redis hosts, and AI credentials load from environment configurations.
