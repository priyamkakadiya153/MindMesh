# Backend Architecture (Part 4 — Database Integration, Background Workers, WebSockets & Event-Driven Processing)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines how MindMesh interacts with databases, manages asynchronous workloads, handles real-time communication, processes AI jobs, and coordinates events across the system.

Every backend implementation must comply with this document.

---

## Data Storage Architecture & Responsibilities
MindMesh partitions data storage by technical responsibility:
1. **PostgreSQL**: Primary source of truth. Stores structured tables (users, rooms, messages, metadata, logs, settings).
2. **Redis**: Cache storage, OTP requests rate-limits, WS state presence, and temporary statuses.
3. **ChromaDB**: Independent vector index. Stores NLP embeddings for semantic retrieval.
4. **Object Storage**: Large binary files (local disk for MVP, S3/MinIO for production). Metadata stays in PostgreSQL.

---

## Background Worker & Asynchronous Strategy
Heavy or expensive operations must run out-of-band to prevent blocking client requests:
* **Background workloads**: PDF parsing, thumbnail generation, embedding vectors, text summarization, and task/decision extractions.
* **Worker Execution**: The API persists the record, commits the transaction, and dispatches a background job. The worker processes the job asynchronously and updates the PostgreSQL record.
* **Retries**: Workers retry transient network or storage failures using exponential backoff.

---

## Domain Event Bus
Domain events decouple business modules without introducing code dependencies:
* **Events**: `MessageSent`, `ConversationCreated`, `FileUploaded`, `SummaryGenerated`, `TaskExtracted`.
* **Payloads**: Lightweight notifications carrying entity primary key identifiers rather than large serialized object models.

---

## WebSocket Push Update Strategy
* WebSockets are strictly unidirectional push updates (new messages, typing indicators, online presence, read receipts, notifications).
* All user actions (creating rooms, sending messages, uploading files) must execute via standard REST APIs.
* **Auth**: Connections are authenticated. Users subscribe to explicit rooms (e.g. `conversation_room`, `user_notification_feed`) to prevent global event broadcasting.
