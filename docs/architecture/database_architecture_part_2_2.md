# Database Architecture (Part 2.2 — Workspace, Projects & Membership Architecture)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the Workspace, Project, and Membership database architecture of MindMesh. It outlines the collaboration boundaries, membership details, and settings mapping that support multi-user collaboration and user workspaces.

---

## Database Tables

### 1. `workspaces` Table
* **Purpose**: Primary workspace container. Every registered user receives a personal workspace.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `owner_id`: UUID (FK -> `users.id`, RESTRICT)
  * `name`: VARCHAR(150) (NOT NULL)
  * `slug`: VARCHAR(150) (UNIQUE, NOT NULL)
  * `description`: TEXT (NULLABLE)
  * `logo_url`: TEXT (NULLABLE)
  * `visibility`: WorkspaceVisibility ENUM (DEFAULT 'PRIVATE')
  * `is_personal`: BOOLEAN (DEFAULT TRUE)
  * `created_at`: TIMESTAMP (NOT NULL)
  * `updated_at`: TIMESTAMP (NOT NULL)
  * `deleted_at`: TIMESTAMP (NULLABLE)

### 2. `workspace_members` Table
* **Purpose**: Maps users to workspaces with specific roles.
* **Columns**:
  * `id`: UUID (PK)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `role`: WorkspaceMemberRole ENUM (Owner, Admin, Member, Guest)
  * `joined_at`: TIMESTAMP (NOT NULL)
  * `invited_by`: UUID (FK -> `users.id`, NULLABLE)
  * `last_active_at`: TIMESTAMP (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)
  * `updated_at`: TIMESTAMP (NOT NULL)
* **Indexes**: Composite index on `(workspace_id, user_id)` (UNIQUE)

### 3. `workspace_settings` Table
* **Purpose**: Stores custom workspace configurations.
* **Columns**:
  * `id`: UUID (PK)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `settings`: JSONB (Stores custom theme keys, upload limits, AI flags, retention policies)
  * `created_at`: TIMESTAMP, `updated_at`: TIMESTAMP

### 4. `projects` Table (Optional Work Organizers)
* **Purpose**: Represents a project channel inside a Workspace. Projects are optional; user channels can exist without project bindings.
* **Columns**:
  * `id`: UUID (PK)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `owner_id`: UUID (FK -> `users.id`, CASCADE)
  * `name`: VARCHAR(255) (NOT NULL)
  * `description`: TEXT (NULLABLE)
  * `status`: ProjectStatus ENUM (Planning, Active, On Hold, Completed, Archived)
  * `color`: VARCHAR(50) (NULLABLE)
  * `icon`: VARCHAR(100) (NULLABLE)
  * `due_date`: TIMESTAMP (NULLABLE)
  * `archived_at`: TIMESTAMP (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)
  * `updated_at`: TIMESTAMP (NOT NULL)
* **Indexes**: `workspace_id`, `status`

### 5. `project_members` Table
* **Purpose**: Maps workspace members to specific projects.
* **Columns**:
  * `id`: UUID (PK)
  * `project_id`: UUID (FK -> `projects.id`, CASCADE)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `role`: ProjectMemberRole ENUM (Owner, Manager, Editor, Contributor, Viewer)
  * `joined_at`: TIMESTAMP (NOT NULL)
  * `assigned_by`: UUID (FK -> `users.id`, NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)
* **Indexes**: Composite index on `(project_id, user_id)` (UNIQUE)

### 6. `project_settings` Table
* **Purpose**: Stores project-specific configurations.
* **Columns**:
  * `id`: UUID (PK)
  * `project_id`: UUID (FK -> `projects.id`, CASCADE)
  * `settings`: JSONB (Stores custom visibility tokens, notifications, permissions)
  * `created_at`: TIMESTAMP, `updated_at`: TIMESTAMP

---

## Indexing Strategy
* **Foreign Keys**: `workspace_id`, `owner_id`, `project_id`, `user_id`.
* **Composite Indexes**:
  * `(workspace_id, user_id)` (facilitates workspace validation checks)
  * `(project_id, user_id)` (facilitates project permission checks)
  * `(workspace_id, status)` (for dashboard queries)
