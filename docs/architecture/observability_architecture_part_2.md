# Observability Architecture (Part 2 — Business Analytics, AI Analytics, User Telemetry & Operational Intelligence)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines how MindMesh measures business performance, AI quality, user behavior, operational health, and product success. It extends traditional observability into business metrics, user journeys, feature adoption, and cost tracking.

---

## Metric Levels & Event Collection
MindMesh measures product success across four layers:

```text
Infrastructure (Memory/CPU) -> Application (APIs/Workers) -> AI Intelligence (Precision/Citations) -> Business Value (DAU/WAU/Retention)
```

* **Event-Driven**: Business metrics are derived from lightweight transactional events (e.g. `workspace_created`, `file_uploaded`, `search_performed`) rather than running heavy queries directly against the PostgreSQL tables.
* **Event schema**: Analytics events are immutable, containing `event_id`, `event_name`, `timestamp`, `user_id`, `workspace_id`, and client device details.

---

## Analytics Sub-systems

### 1. User & Workspace Telemetry
* Tracks user adoption (Daily/Weekly/Monthly Active Users, session durations) and workspace growth metrics (storage footprints, workspace retention).

### 2. Search & Document Intelligence
* Tracks search latency, semantic vs. keyword ratios, zero-result searches, file preview generation speed, and OCR processing queues.

### 3. AI & Cost Analytics
* Tracks prompt sizes, completion tokens, model latency, and cost per request.
* Cost allocation reports split expenditures by workspace, model backend (Gemini vs. OpenAI vs. local), and functionality (summarization vs. retrieval).

### 4. RAG Quality Benchmarking
* Continuously evaluates retrieval precision (`Precision@K`, `Recall@K`), ranking quality, empty searches, context utilization, and user accuracy ratings.

---

## Dashboard Views
Observability reporting is structured into four role-specific Grafana views:
* **Executive Dashboard**: High-level workspace growth, total active users, overall data footprint, and monthly AI cost.
* **Product Dashboard**: Feature adoption graphs (Summaries vs. Chat vs. Search), user journey funnels, and onboarding retention.
* **Engineering Dashboard**: API latency curves, worker backlog queue sizes, error rates, and system deployments.
* **AI Dashboard**: Retrieval accuracy ratios, hallucination rates, citation success, model costs, and prompt versions.
