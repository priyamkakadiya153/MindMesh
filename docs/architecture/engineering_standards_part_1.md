# Platform Architecture Completion & Engineering Standards (Part 1 — Cross-Cutting Architecture, Engineering Principles, Coding Standards, Architectural Decision Records & Platform Blueprint)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence Platform

---

## Purpose
This document defines the global engineering standards that apply to every component of MindMesh. It unifies coding casing cases, feature-first directories organization, audit columns requirements, Architectural Decision Records (ADR) schemas, and quality gate checklists.

Every future feature, merge request, and architecture modification must comply with this document.

---

## Clean Architecture & Dependency Direction
MindMesh conforms strictly to Clean Architecture layer divisions:

```text
Presentation Layer (UI/Views) -> Application Layer (Services) -> Domain Layer (Entities/Rules) -> Infrastructure Layer (DB/API/Storage adapters)
```

* **Domain Isolation**: The Domain Layer represents pure business concepts and is completely independent of frameworks, databases, or routing protocols.
* **Dependencies Rule**: Dependencies point exclusively inward. Outer layers (e.g. database adapters) implement interfaces defined by inner layers (Domain/Application).

---

## Repository & Directory Standards
* **Feature-First Organization**: Folders are structured by domain features (e.g., `knowledge/`, `search/`, `workflow/`, `ai/`) rather than technical types (`controllers/`, `services/`, `repositories/`).
* **Granular Component Scopes**:
  * **Controllers**: Strictly parse/validate payloads and return responses.
  * **Services**: Handle core workflow transactions and validations.
  * **Repositories**: Manage database query executions and connection sessions.

---

## Coding, Database & Naming Standards

### 1. Naming Cases
* `PascalCase`: Classes, Types, Interfaces.
* `camelCase`: Properties, Variables, Functions.
* `snake_case`: Database tables, columns, parameters.
* `kebab-case`: Router URL paths.

### 2. Standard Audit Columns
Every relational table schema must define the following metadata columns:
`id` (UUIDv7/v4), `created_at`, `updated_at`, `deleted_at` (soft deletes support), `created_by`, `updated_by`.

---

## Architectural Decision Records (ADR)
Every major technical decision or structural change requires registering an ADR file:
* **ADR Schema**: Tracks `Title`, `Context`, `Decision`, `Alternatives Evaluated`, `Consequences`, `Status` (Proposed, Approved, Implemented, Deprecated), `Date`, and `Owner`.
* **ADR Lifecycle**: Proposals must pass review gates before code execution.

---

## Engineering Quality Gates
Pull requests require verification checks before promotion:
1. **Architecture Compliance Check**: Verifies layer directions and feature-first setups.
2. **Automated Testing**: Passing unit and integration tests under coverage limits.
3. **Structured Logging & Telemetry Audits**.
4. **Security Vulnerability Scans**.
