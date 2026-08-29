# 20.3 — Enterprise Database Architecture, PostgreSQL Schema, SQLAlchemy Models, Alembic Migrations & Data Layer Implementation

**Project:** MindMesh – AI-Powered Knowledge Intelligence Platform

**Phase:** Phase 20 — Enterprise Implementation Blueprint & Production Development

**Document Version:** 1.0

**Document Type:** Database Layer Implementation Guide

**Status:** Production Implementation Blueprint

**Classification:** Database Engineering Guide

**Architecture Authority:** Engineering Leadership

**Owners:**

* Chief Technology Officer
* Backend Engineering Team
* Platform Engineering Team
* API Team
* Infrastructure Team

---

# Purpose

This document defines the **database implementation layer** for MindMesh.

It establishes the physical PostgreSQL schema, SQLAlchemy models, migration workflow with Alembic, repository abstraction patterns, indexing strategies, relationship mappings, and data-seeding setups.

This is a **runnable and validated component** of the MindMesh platform.

---

# Tech Stack

| Component | Technology |
|-----------|------------|
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.x |
| Migration | Alembic |
| Validation | Pydantic v2 |
| Driver | asyncpg |
| UUID | PostgreSQL UUID |

---

# Folder Structure

```text
backend/
├── app/
│   ├── database/
│   │   ├── connection.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── seed.py
│   ├── models/
│   │   ├── base.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── workspace.py
│   │   ├── project.py
│   │   ├── document.py
│   │   ├── chat.py
│   │   ├── message.py
│   │   ├── task.py
│   │   ├── agent.py
│   │   └── audit.py
│   ├── repositories/
│   │   └── base.py
│   ├── core/
│   │   └── database.py
│   └── main.py
└── alembic.ini
```

---

# Database Architecture

```text
FastAPI
   ↓
Service Layer
   ↓
Repository Layer
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL
```

---

# Base Entity

Every table inherits: `BaseEntity`

Contains:
* `id` (UUID, Primary Key)
* `created_at` (DateTime, Default: UTC Now)
* `updated_at` (DateTime, Default: UTC Now)
* `created_by` (String, Optional)
* `updated_by` (String, Optional)
* `deleted_at` (DateTime, Optional)
* `is_active` (Boolean, Default: True)

---

# Core Tables

* `users`
* `organizations`
* `organization_members`
* `workspaces`
* `projects`
* `documents`
* `document_chunks`
* `chats`
* `messages`
* `tasks`
* `agents`
* `agent_memory`
* `audit_logs`

---

# Relationships

```text
Organization
     ↓
Workspace
     ↓
Project
     ↓
Documents
     ↓
Chunks
```

```text
Users
  ↓
Chats
  ↓
Messages
```

---

# UUID Strategy

Every primary key uses: `UUID`.
Never use auto-increment integer IDs for domain entities.

---

# Naming Convention

* Tables: `snake_case`
* Columns: `snake_case`
* Foreign Keys: `user_id`, `project_id`, `organization_id`

---

# Database Indexes

Create indexes for:
* `email`
* `username`
* `project_id`
* `organization_id`
* `document_id`
* `created_at`
* `updated_at`

### Composite Indexes
* `(project_id, created_at)`
* `(document_id, chunk_index)`

---

# Soft Delete

Every table implements soft delete using `deleted_at` and `is_active` fields.
No permanent database record deletion by default.

---

# Multi-Tenancy

Every business-tenant table contains an index-mapped `organization_id` to ensure absolute tenant data isolation.

---

# Alembic Migration Workflow

```text
Create Model
     ↓
Generate Migration
     ↓
Review SQL
     ↓
Apply Migration
     ↓
Run Tests
```

### Commands
```bash
alembic revision --autogenerate
alembic upgrade head
```

---

# Seed Data

Upon startup, the system automatically runs a seed script creating:
* System Admin User
* Default Organization
* Default Workspace
* Default Sample Project
* System Roles
* Permissions

---

# Repository Pattern

```text
Router
  ↓
Service
  ↓
Repository
  ↓
Database
```

API layers should never access database sessions directly.

---

# Transactions

Business operations manage transaction states explicitly:
```text
BEGIN
  ↓
Update Data
  ↓
Commit
  ↓
Rollback on Error
```

---

# Deliverables

This chapter implements:
* ✅ PostgreSQL Connection Pool Configuration
* ✅ SQLAlchemy Async Engine Integration
* ✅ Base Entities & Auditing Fields
* ✅ Comprehensive Relational Database Schema
* ✅ Alembic Async Migration Environment
* ✅ Automated DB Seeding Script
* ✅ Generic Async Repository Pattern
* ✅ UUID Generation and Multi-Tenant Isolation

---

# Relationship to Previous Architecture

This architecture extends:

* **Phase 20.2 (Frontend Project Skeleton)**: [frontend_project_skeleton_nextjs_foundation_design_system_client_application_architecture.md](file:///d:/7%20sem/MindMesh/docs/architecture/frontend_project_skeleton_nextjs_foundation_design_system_client_application_architecture.md)
* **Phase 20.1 (Backend Project Skeleton)**: [backend_project_skeleton_fastapi_foundation_core_service_architecture.md](file:///d:/7%20sem/MindMesh/docs/architecture/backend_project_skeleton_fastapi_foundation_core_service_architecture.md)
* **Phase 20.0 (Monorepo Setup)**: [monorepo_setup_repository_initialization.md](file:///d:/7%20sem/MindMesh/docs/architecture/monorepo_setup_repository_initialization.md)
* **Phase 16.3 (Database Architecture)**: [enterprise_database_architecture_polyglot_persistence_distributed_storage_data_engineering_platform.md](file:///d:/7%20sem/MindMesh/docs/architecture/enterprise_database_architecture_polyglot_persistence_distributed_storage_data_engineering_platform.md)

---

# Next Document

## **20.4 — Enterprise Authentication, JWT Security, OAuth2 Integration & Multi-Tenant Role-Based Access Control**

The next document defines the enterprise authentication, authorization, and tenant isolation model, including user registration, login, JWT validation, roles, and permissions mapping.

Link: [enterprise_authentication_jwt_security_oauth2_integration_multi_tenant_rbac.md](file:///d:/7%20sem/MindMesh/docs/architecture/enterprise_authentication_jwt_security_oauth2_integration_multi_tenant_rbac.md)

