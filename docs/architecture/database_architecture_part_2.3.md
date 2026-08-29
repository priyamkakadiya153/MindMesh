# Database Architecture (Part 2.3 — Conversations, Messages & Communication Architecture)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the complete communication database architecture of MindMesh. It covers conversation metadata, member roles, thread hierarchies, message revisions, emoji reactions, user mentions, read receipt tracking, and message pins.

---

## Database Tables

### 1. `conversations` Table
* **Purpose**: Primary chat space details.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `project_id`: UUID (FK -> `projects.id`, CASCADE, NULLABLE)
  * `created_by`: UUID (FK -> `users.id`, RESTRICT)
  * `title`: VARCHAR(255) (NULLABLE for Direct Messages)
  * `description`: TEXT (NULLABLE)
  * `type`: ConversationType ENUM (GENERAL, PROJECT, DIRECT_MESSAGE, GROUP, PRIVATE)
  * `is_private`: BOOLEAN (DEFAULT FALSE)
  * `is_archived`: BOOLEAN (DEFAULT FALSE)
  * `last_message_at`: TIMESTAMP (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)
  * `updated_at`: TIMESTAMP (NOT NULL)
  * `deleted_at`: TIMESTAMP (NULLABLE)

### 2. `conversation_members` Table
* **Purpose**: Maps users to active conversations they are participating in.
* **Columns**:
  * `id`: UUID (PK)
  * `conversation_id`: UUID (FK -> `conversations.id`, CASCADE)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `role`: ConversationMemberRole ENUM (Owner, Moderator, Member, Guest)
  * `joined_at`: TIMESTAMP (NOT NULL)
  * `last_read_message_id`: UUID (FK -> `messages.id`, NULLABLE)
  * `last_seen_at`: TIMESTAMP (NULLABLE)
  * `is_muted`: BOOLEAN (DEFAULT FALSE)
  * `is_pinned`: BOOLEAN (DEFAULT FALSE)
* **Indexes**: Composite index on `(conversation_id, user_id)` (UNIQUE)

### 3. `messages` Table (Immutable Primary Logs)
* **Purpose**: Primary message entries. Modifications do not overwrite rows directly; they generate entries in `message_versions`.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `conversation_id`: UUID (FK -> `conversations.id`, CASCADE)
  * `sender_id`: UUID (FK -> `users.id`, RESTRICT)
  * `parent_message_id`: UUID (FK -> `messages.id`, CASCADE, NULLABLE - handles threaded sub-messages)
  * `reply_to_message_id`: UUID (FK -> `messages.id`, SET NULL, NULLABLE - points to the visual message being quoted)
  * `message_type`: MessageType ENUM (TEXT, IMAGE, VIDEO, DOCUMENT, AUDIO, VOICE_NOTE, SYSTEM, TASK, DECISION, FILE_REFERENCE)
  * `content`: TEXT (NOT NULL)
  * `metadata`: JSONB (NULLABLE - stores custom attachment sizing, link previews, or task details)
  * `is_edited`: BOOLEAN (DEFAULT FALSE)
  * `is_deleted`: BOOLEAN (DEFAULT FALSE)
  * `created_at`: TIMESTAMP (NOT NULL)
  * `updated_at`: TIMESTAMP (NOT NULL)

### 4. `message_versions` Table (Edit History Audit Log)
* **Purpose**: Tracks previous edits to maintain data auditability.
* **Columns**:
  * `id`: UUID (PK)
  * `message_id`: UUID (FK -> `messages.id`, CASCADE)
  * `version`: INT (NOT NULL)
  * `content`: TEXT (NOT NULL)
  * `edited_by`: UUID (FK -> `users.id`, RESTRICT)
  * `edited_at`: TIMESTAMP (NOT NULL)

### 5. `message_reactions` Table
* **Purpose**: Tracks emoji reactions on individual message logs.
* **Columns**:
  * `id`: UUID (PK)
  * `message_id`: UUID (FK -> `messages.id`, CASCADE)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `emoji`: VARCHAR(50) (NOT NULL)
  * `created_at`: TIMESTAMP (NOT NULL)
* **Indexes**: Composite index on `(message_id, user_id, emoji)` (UNIQUE)

### 6. `message_mentions` Table
* **Purpose**: Identifies users tagged in message logs to trigger async notifications.
* **Columns**:
  * `id`: UUID (PK)
  * `message_id`: UUID (FK -> `messages.id`, CASCADE)
  * `mentioned_user_id`: UUID (FK -> `users.id`, CASCADE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 7. `pinned_messages` Table
* **Purpose**: Stores pinned messages within active workspaces.
* **Columns**:
  * `id`: UUID (PK)
  * `conversation_id`: UUID (FK -> `conversations.id`, CASCADE)
  * `message_id`: UUID (FK -> `messages.id`, CASCADE)
  * `pinned_by`: UUID (FK -> `users.id`, RESTRICT)
  * `pinned_at`: TIMESTAMP (NOT NULL)

### 8. `read_receipts` Table
* **Purpose**: Maps user reads across message logs.
* **Columns**:
  * `id`: UUID (PK)
  * `message_id`: UUID (FK -> `messages.id`, CASCADE)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `read_at`: TIMESTAMP (NOT NULL)
* **Indexes**: Composite index on `(message_id, user_id)` (UNIQUE)

---

## Indexing Strategy
* **Foreign Keys**: `conversation_id`, `sender_id`, `parent_message_id`.
* **Composite Indexes**:
  * `(conversation_id, created_at)` (for listing messages ordered by timeline)
  * `(sender_id, created_at)` (for user message metrics)
  * `(conversation_id, message_type)` (for media file browsing filtering)
