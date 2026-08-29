# Real-Time Architecture (Part 2 — Collaboration Engine, Live File Collaboration, Event Streaming & Conflict Resolution)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines how multiple users collaborate simultaneously inside MindMesh. It specifies live file collaboration discussions, AI pipeline events, optimistic UI rollbacks, event replay upon reconnection, conflict validation, and event idempotency.

---

## Live File & AI Collaboration
* **File Hubs**: Every uploaded file acts as a collaborative space. Users can comment, view previews, and track version history. Modifying file details triggers real-time events.
* **AI Progress Updates**: AI generation events (`SummaryStarted`, `SummaryCompleted`, `EmbeddingStarted`, `TaskExtractionCompleted`) stream to the client to update loading skeletons or progress bars dynamically.

---

## Event Pipeline & Reconnection Replay

### 1. Streaming Pipeline
```text
Business Service -> Domain Event -> Event Bus -> Redis Pub/Sub -> WS Subscribers -> Client UI
```

### 2. Event Replay Upon Reconnect
* Clients track the `Last Event ID` received before a disconnect.
* Upon reconnecting, the client requests a replay of missing event logs to reconcile local cache without full-page reloads.

---

## Optimistic UI & Version Control

### 1. Optimistic UI Updates
* The client UI registers action mutations immediately (e.g. adding a message draft).
* If server-side database constraint validation fails, the UI rolls back the optimistic changes.

### 2. Version Synchronization
* Collaboration objects track numeric increment version schemas.
* **Conflict Resolution**: Enforces server-authoritative validation check. When concurrent edits conflict, the server accepts the latest valid version and rejects/notifies stale version updates (preventing silent overwrites).

---

## Event Ordering & Idempotency Rules
* **Strict Ordering**: Ordered event timelines are maintained within a single conversation room using sequential IDs and timestamps.
* **Idempotency**: Event handlers are idempotent. Duplicate event frames from network retry cycles must be ignored, ensuring no duplicate messages or transactions are written.
