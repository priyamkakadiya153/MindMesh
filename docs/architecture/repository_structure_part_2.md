# Repository Structure (Part 2 — Applications & Monorepo Structure)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the application layer of the MindMesh monorepo. Applications are executable software systems that consume shared packages but must never contain reusable business logic that belongs in shared packages.

---

## Application Philosophy
MindMesh follows a **Monorepo with Multiple Applications**. Each application represents a deployable unit. Applications communicate using well-defined APIs and shared contracts.

During the MVP phase, **only two applications are allowed**:
* **Web Application** (`apps/web/`): User Interface and client-side presentation.
* **Backend API** (`apps/api/`): Core business logic, database operations, and AI.

No additional applications may be created without updating the architecture documentation.

---

## Folder Hierarchy & Responsibilities

### apps/web
The Web Application is responsible for UI rendering, client-side routing, state management, and user interaction.
* **Contains**: React, Vite, TypeScript, Tailwind CSS, Zustand.
* **Structure**:
  ```text
  apps/web/
  ├── public/
  ├── src/
  ├── tests/
  ├── package.json
  ├── tsconfig.json
  ├── vite.config.ts
  ├── tailwind.config.ts
  └── index.html
  ```
* **Constraint**: Must never access the database directly, run SQL queries, or store backend secrets.

### apps/api
The Backend API is responsible for API routing, validation, business rules, persistence, real-time WebSockets, and AI coordination.
* **Contains**: FastAPI (Python), Alembic (database migrations), SQLAlchemy/SQLModel (ORM), Uvicorn.
* **Structure**:
  ```text
  apps/api/
  ├── app/
  ├── tests/
  ├── alembic/
  ├── pyproject.toml
  ├── requirements.txt
  ├── Dockerfile
  └── main.py
  ```
* **Constraint**: Must never contain UI assets, frontend templates, or presentation code.

---

## Communication and Dependency Rules
* **Dependency Direction**: Applications depend on Packages. Packages must never depend on Applications.
* **Communication Rules**: The Web Application communicates with the Backend API exclusively via REST APIs and WebSockets. Direct database or infrastructure connections from the frontend are prohibited.
