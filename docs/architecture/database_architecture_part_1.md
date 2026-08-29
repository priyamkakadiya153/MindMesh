# Database Architecture (Part 1 — Database Design Principles, PostgreSQL Schema & Data Modeling)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official database architecture of MindMesh. It establishes the design principles, relational modeling standards, naming conventions, schema organization, normalization strategy, indexing rules, migration workflow, and data integrity policies.

---

## Database Engine & Schema Strategy
* **Database**: PostgreSQL 17+ (primary source of truth for all business entities).
* **Isolation**: Single application database separated logically by domain tables rather than multiple physical databases.
* **Normalization**: Third Normal Form (3NF) is target standard. Comma-separated listings are prohibited; many-to-many relationships must use explicit junction tables.

---

## Primary Keys & Reference Constraints

### 1. Primary Keys (UUID)
* Business tables must use **UUID Version 7** (preferred) or **UUID Version 4** (fallback).
* Auto-increment integers are prohibited for primary keys.

### 2. Relationships & Integrity
* Relational joins must be enforced using database-level Foreign Keys.
* DB-level constraints (Unique constraints, NOT NULL, Check constraints) must be implemented. Application validations complement but do not replace database constraints.

### 3. Naming Conventions
* **Tables**: Plural nouns (e.g. `users`, `conversations`).
* **Columns**: `snake_case` (e.g. `created_at`, `mobile_number`).
* **Booleans**: Descriptive prefixed flags (e.g. `is_active`, `is_archived`).
* **Enums**: Native PostgreSQL enums (`UserRole`, `MessageType`).

---

## Soft Deletes & Auditing
Every business table must include the following audit timestamp columns:
* `created_at`: Immutable UTC creation timestamp.
* `updated_at`: Automatically updated on row updates.
* `deleted_at`: UTC timestamp when soft-deleted, or `NULL` if active.

*Soft delete policy*: Rows are soft-deleted by default to maintain AI indexes and audit history. Permanent rows deletion is restricted to admin maintenance operations.

---

## Alembic Migration Guidelines
* Schema changes are versioned exclusively through **Alembic** migrations.
* Direct manual table modifications in staging or production environments are prohibited.
* Migrations must be reviewable in the code history, with one change per migration.
