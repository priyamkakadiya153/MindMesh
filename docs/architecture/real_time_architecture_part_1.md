# Real-Time Architecture (Part 1 — WebSockets, Presence, Event Bus & Live Collaboration)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the complete real-time communication architecture of MindMesh. It covers the WebSocket connection lifecycle, Redis presence, typing indicators, read receipts, event bus coordination, and real-time AI statuses.

Every real-time component must comply with this document.

---

## WebSocket & REST Division of Labor
* **REST APIs**: Responsible for CRUD operations, authentication verification, settings configuration, and raw search queries.
* **WebSockets**: Responsible strictly for live event updates (typing states, new messages, read receipts, notifications, AI processing steps, upload progress).
* *Rule*: WebSockets must never replace REST APIs for state mutation. Persistence in the database must occur *before* broadcasting.

---

## Connection Lifecycle & Room Architecture

### 1. Connection Lifecycle
* **Authentication**: Upgrade request validates the user's JWT. Authenticated connections join specific rooms.
* **Stale Cleanup**: Periodic heartbeats prune inactive sockets.

### 2. Room Architecture
* Users subscribe only to relevant rooms:
  * `Workspace Room`
  * `Project Room`
  * `Conversation Room` (for chat history)
  * `Notification Room` (for user-specific alerts)
  * `AI Processing Room` (for prompt status logs)
* *Rule*: Global broadcasts are prohibited. Sockets receive events only for rooms they are explicitly authorized to join.

---

## Presence, Indicators & Receipts

### 1. Redis Presence System
* Statuses (`Online`, `Away`, `Busy`, `Offline`, `Invisible`) are tracked in Redis.
* Connect, activity check-ins, and disconnects automatically sync state to Redis.

### 2. Typing Indicators
* Typing triggers are ephemeral broadcasts.
* *Rule*: Typing indicators must never be persisted in PostgreSQL.

### 3. Read Receipts
* Real-time read receipt updates sync database message receipts and broadcast status changes to other participants.

---

## Event Bus & Reliability
* **Domain Events**: `MessageSent`, `MessageEdited`, `MessageDeleted`, `ConversationCreated`, `FileUploaded`, `SummaryGenerated`.
* **Ordering**: Chronological message ordering within a single conversation is enforced.
* **Handlers**: Event handlers are idempotent to safely handle duplicate network events.

---

## Performance Targets
* **Connection Upgrade**: < 300 ms
* **Message Broadcast**: < 100 ms
* **Typing Indicator**: < 100 ms
* **Presence Update**: < 150 ms
* **Notification Delivery**: < 200 ms
