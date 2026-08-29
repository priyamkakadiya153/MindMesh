# Backend Architecture (Part 2 — Domain Architecture, Service Layer & Repository Pattern)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the internal organization of backend business domains, the Service Layer, Repository Pattern, Domain ownership, Dependency Injection strategy, transaction management, and communication rules.

Every backend implementation must comply with this document.

---

## Domain-Driven Philosophy & Ownership
MindMesh is organized around independent business capabilities (Domains) rather than technical layers. Every domain owns its complete slice:

```text
domains/<name>/
├── api/             # HTTP Route handlers
├── services/        # Business workflows and logic
├── repositories/    # Pure database queries (CRUD, filters, paging)
├── models/          # Relational entities (SQLModel definitions)
├── schemas/         # Request and Response Pydantic DTO models
└── validators/      # Custom validation rules
```

No other domain may modify another domain's internal code or models directly.

---

## Domain Communication & Layering Rules

### 1. Cross-Domain Communication
* Domains communicate **exclusively through Services**.
* **Allowed**: `ConversationService` -> `MessageService`.
* **Prohibited**: `ConversationRepository` -> `MessageRepository` (Repositories must remain isolated and never import or invoke other repositories).

### 2. Service Layer Boundaries
* The service layer acts as the stateless orchestrator. It manages business rules, coordinates repository actions, maps transactions, and invokes AI pipelines.
* *Constraint*: All business checks (e.g. "is user a member of this chat room?", "enforce upload limits") belong inside services.

### 3. Repository Constraints
* Repositories abstract the database. They perform CRUD, query filtering, database joins, and paging.
* *Constraint*: Repositories must never perform email dispatching, call external APIs, perform business validation, or execute AI embeddings queries.

---

## Transaction & Dependency Management
* **Transactions**: Transactions are managed at the **Service layer**. If a multi-step business process (e.g., creating a room and inserting the first welcome message) fails midway, the service layer handles the rollback.
* **Dependency Injection**: Dependencies (database sessions, repositories, Redis clients, configuration variables) are injected into service and controller constructors. Manual instantiation inside business services is prohibited.
