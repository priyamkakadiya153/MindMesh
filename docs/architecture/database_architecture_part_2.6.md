# Database Architecture (Part 2.6 — Search, Notifications, Activity Logs, Analytics & System Architecture)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the database tables supporting universal search, workspace notification preferences, activity timelines, security compliance audit logging, anonymized analytics, external integrations, and global system configuration parameters.

Every database object must comply with this document.

---

## Database Tables

### 1. `search_history` Table
* **Purpose**: Tracks search activity for suggestions and recency lists.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `query`: TEXT (NOT NULL)
  * `search_type`: SearchType ENUM (Keyword, Semantic, Hybrid, File, Conversation, Knowledge, AI)
  * `filters`: JSONB (NULLABLE - stores date ranges, file tags, user constraints)
  * `result_count`: INT (DEFAULT 0)
  * `execution_time`: FLOAT (NOT NULL - time in seconds)
  * `created_at`: TIMESTAMP (NOT NULL)

### 2. `saved_searches` Table
* **Purpose**: Stores intelligent filtering definitions for quick access.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `title`: VARCHAR(255) (NOT NULL)
  * `query`: TEXT (NOT NULL)
  * `filters`: JSONB (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 3. `notifications` Table
* **Purpose**: Tracks direct notifications sent to users.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `type`: NotificationType ENUM (INFO, SUCCESS, WARNING, ERROR, SYSTEM)
  * `title`: VARCHAR(255) (NOT NULL)
  * `message`: TEXT (NOT NULL)
  * `entity_type`: VARCHAR(100) (NOT NULL)
  * `entity_id`: UUID (NOT NULL)
  * `is_read`: BOOLEAN (DEFAULT FALSE)
  * `read_at`: TIMESTAMP (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 4. `notification_preferences` Table
* **Purpose**: Stores user communication settings.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `preferences`: JSONB (NOT NULL - stores email flags, desktop alerts, and muting setups)
  * `created_at`: TIMESTAMP, `updated_at`: TIMESTAMP

### 5. `activity_logs` Table (Work Timeline Feed)
* **Purpose**: Tracks business action histories to assemble workspace dashboards and team timelines.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `activity_type`: VARCHAR(100) (NOT NULL - e.g. `message_sent`, `file_uploaded`)
  * `entity_type`: VARCHAR(100) (NOT NULL)
  * `entity_id`: UUID (NOT NULL)
  * `metadata`: JSONB (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 6. `audit_logs` Table (Immutable Compliance Log)
* **Purpose**: Immutably tracks security-sensitive events (Role additions, file deletions).
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, RESTRICT - user deletion must block if audit logs exist, or assign to system)
  * `action`: VARCHAR(150) (NOT NULL)
  * `resource`: VARCHAR(100) (NOT NULL)
  * `resource_id`: UUID (NOT NULL)
  * `ip_address`: VARCHAR(45) (NOT NULL)
  * `device`: VARCHAR(255) (NOT NULL)
  * `created_at`: TIMESTAMP (NOT NULL)
* *Rule*: Audit log entries are strictly append-only. Deletes or updates on this table are prohibited.

### 7. `analytics_events` Table (Anonymized Usage Log)
* **Purpose**: Tracks platform features traffic anonymously to improve application flows.
* **Columns**:
  * `id`: UUID (PK)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `event_name`: VARCHAR(150) (NOT NULL)
  * `properties`: JSONB (NOT NULL)
  * `created_at`: TIMESTAMP (NOT NULL)

### 8. `feature_usage` Table
* **Purpose**: Tracks aggregated usage statistics for dashboard rendering.
* **Columns**:
  * `id`: UUID (PK)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `feature_name`: VARCHAR(100) (NOT NULL - e.g. `total_messages`, `storage_size`)
  * `usage_count`: INT (DEFAULT 0)
  * `storage_used`: BIGINT (DEFAULT 0)
  * `created_at`: TIMESTAMP, `updated_at`: TIMESTAMP

### 9. `integrations` Table
* **Purpose**: Tracks external services connected to a workspace.
* **Columns**:
  * `id`: UUID (PK)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `provider`: VARCHAR(100) (NOT NULL - e.g. `google_drive`, `github`)
  * `status`: VARCHAR(50) (NOT NULL)
  * `configuration`: JSONB (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 10. `integration_tokens` Table (Encrypted Credentials)
* **Purpose**: Stores external API tokens securely.
* **Columns**:
  * `id`: UUID (PK)
  * `integration_id`: UUID (FK -> `integrations.id`, CASCADE)
  * `token_type`: VARCHAR(100) (NOT NULL)
  * `encrypted_token`: TEXT (NOT NULL - credentials must always be stored encrypted)
  * `expires_at`: TIMESTAMP (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 11. `system_settings` Table (Global Configuration)
* **Purpose**: Global key-value configs (e.g. max upload size).
* **Columns**:
  * `id`: UUID (PK)
  * `key`: VARCHAR(100) (UNIQUE, NOT NULL)
  * `value`: TEXT (NOT NULL)
  * `description`: TEXT (NULLABLE)
  * `updated_by`: UUID (FK -> `users.id`, RESTRICT)
  * `updated_at`: TIMESTAMP (NOT NULL)

---

## Indexing Strategy
* **Foreign Keys**: `user_id`, `workspace_id`, `integration_id`.
* **Composite Indexes**:
  * `(user_id, created_at)` (for loading history)
  * `(workspace_id, created_at)` (for workspace timeline logs)
  * `(user_id, is_read)` (for notification badges)
  * `(event_name, created_at)` (for usage analytics)
