# Database Architecture (Part 2.5 — AI Knowledge Engine, RAG & Organizational Memory Architecture)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the AI Knowledge Engine schema of MindMesh. It covers background jobs tracking, AI summaries, extracted task listings, extracted decision logs, persistent organizational memories, RAG query context caches, and user feedback audits.

---

## Database Tables

### 1. `ai_jobs` Table (Task Tracking Audit)
* **Purpose**: Tracks execution state for asynchronous AI processing jobs.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `job_type`: VARCHAR(100) (NOT NULL - e.g. `summary`, `task_extraction`, `embeddings`)
  * `entity_type`: VARCHAR(100) (NOT NULL - e.g. `conversation`, `file`)
  * `entity_id`: UUID (NOT NULL)
  * `status`: AIJobStatus ENUM (Pending, Queued, Running, Completed, Failed, Cancelled)
  * `priority`: INT (DEFAULT 0)
  * `started_at`: TIMESTAMP (NULLABLE)
  * `completed_at`: TIMESTAMP (NULLABLE)
  * `error_message`: TEXT (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 2. `conversation_summaries` Table
* **Purpose**: Stores versioned summaries generated automatically for conversations.
* **Columns**:
  * `id`: UUID (PK)
  * `conversation_id`: UUID (FK -> `conversations.id`, CASCADE)
  * `summary`: TEXT (NOT NULL)
  * `model`: VARCHAR(100) (NOT NULL)
  * `version`: INT (NOT NULL - summary versions start at 1)
  * `generated_at`: TIMESTAMP (NOT NULL)

### 3. `extracted_tasks` Table
* **Purpose**: Stores actionable tasks automatically extracted from messaging logs.
* **Columns**:
  * `id`: UUID (PK)
  * `conversation_id`: UUID (FK -> `conversations.id`, CASCADE)
  * `message_id`: UUID (FK -> `messages.id`, CASCADE, NULLABLE)
  * `title`: VARCHAR(255) (NOT NULL)
  * `description`: TEXT (NULLABLE)
  * `assigned_to`: UUID (FK -> `users.id`, NULLABLE)
  * `due_date`: TIMESTAMP (NULLABLE)
  * `priority`: VARCHAR(50) (NULLABLE)
  * `status`: TaskStatus ENUM (Open, In Progress, Completed, Cancelled)
  * `confidence`: FLOAT (NOT NULL - AI confidence score)
  * `created_at`: TIMESTAMP (NOT NULL)

### 4. `extracted_decisions` Table
* **Purpose**: Tracks structural decisions made inside conversation history.
* **Columns**:
  * `id`: UUID (PK)
  * `conversation_id`: UUID (FK -> `conversations.id`, CASCADE)
  * `message_id`: UUID (FK -> `messages.id`, CASCADE, NULLABLE)
  * `decision`: TEXT (NOT NULL)
  * `reason`: TEXT (NULLABLE)
  * `confidence`: FLOAT (NOT NULL - AI confidence score)
  * `created_at`: TIMESTAMP (NOT NULL)

### 5. `ai_memories` Table (High-Value Persistent Knowledge)
* **Purpose**: Stores long-term organizational context blocks (Architecture rules, Standards).
* **Columns**:
  * `id`: UUID (PK)
  * `workspace_id`: UUID (FK -> `workspaces.id`, CASCADE)
  * `project_id`: UUID (FK -> `projects.id`, CASCADE, NULLABLE)
  * `title`: VARCHAR(255) (NOT NULL)
  * `content`: TEXT (NOT NULL)
  * `importance`: INT (DEFAULT 0)
  * `source`: VARCHAR(255) (NOT NULL - source message/file ID link)
  * `created_at`: TIMESTAMP (NOT NULL)

### 6. `rag_contexts` Table (Query Retrieval Cache)
* **Purpose**: Temporary cache storing vector context search answers to prevent query repetition.
* **Columns**:
  * `id`: UUID (PK)
  * `query_hash`: VARCHAR(64) (UNIQUE, NOT NULL - SHA-256 hash of the text query)
  * `retrieved_chunks`: JSONB (NOT NULL - JSON array of retrieved text blocks)
  * `retrieval_score`: FLOAT (NOT NULL)
  * `expires_at`: TIMESTAMP (NOT NULL)

### 7. `prompt_history` Table
* **Purpose**: Audit log tracking prompt execution metrics.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `prompt_type`: VARCHAR(100) (NOT NULL)
  * `model`: VARCHAR(100) (NOT NULL)
  * `token_usage`: INT (NOT NULL)
  * `response_time`: INT (NOT NULL - time in ms)
  * `created_at`: TIMESTAMP (NOT NULL)

### 8. `ai_feedback` Table
* **Purpose**: Collects explicit user feedback on LLM generation accuracy.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `response_id`: UUID (NOT NULL - ID of the generation entity)
  * `rating`: INT (NOT NULL - score value like 1 or -1)
  * `feedback`: TEXT (NULLABLE)
  * `created_at`: TIMESTAMP (NOT NULL)

### 9. `ai_usage_logs` Table (Analytics Audit)
* **Purpose**: Monitors prompt traffic and token usage logs.
* **Columns**:
  * `id`: UUID (PK)
  * `request_metadata`: JSONB (NOT NULL)
  * `created_at`: TIMESTAMP (NOT NULL)
