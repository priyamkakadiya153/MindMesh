# Workflow Automation Architecture (Part 2 — Workflow Orchestration, Distributed Execution, Saga Pattern, Compensation & Enterprise Automation Platform)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence Platform

---

## Purpose
This document defines the enterprise-grade orchestration layer that coordinates all workflows inside MindMesh. It specifies Directed Acyclic Graph (DAG) executors, distributed task schedulers, checkpoint savers, Saga rollbacks, and versioning parameters.

---

## DAG Execution & Scheduler
* **DAG Layout**: Workflows are converted to Directed Acyclic Graphs (DAGs) defining explicit block dependencies.
* **Orchestrator Role**: Manages parallel execution nodes, monitors step dependencies, aggregates worker completions, and enforces SLA limits.
* **Task Scheduler**: Distributes step operations across specific queues (AI Workers, OCR, Search indexers) avoiding direct service-to-service calls.

---

## Checkpointing & State Durability
* **Checkpoint Persistence**: Long-running workflows persist context state to the database after completing key milestone steps (checkpoints).
* **Crash Recovery**: If a worker node crashes mid-execution, the Scheduler references the last checkpoint state to resume processing instead of restarting the entire pipeline.

---

## Saga Pattern & Compensation Transactions
MindMesh avoids heavy distributed database transactions across services using the Saga Pattern:
* **Saga Pipeline**: A chain of isolated local service transactions.
* **Compensation Actions**: Each step defines a matching reverse action (compensation transaction) to execute if a downstream task fails:

```text
Step 1: Create Project Space -> Step 2: Create Storage Folder -> Step 3: Index Chunks (FAIL)
                                                                           │
                                                                           ▼
Rollback Storage Folder <─── Rollback Project Space <─── Trigger Compensation Engine
```

---

## Versioning & Migration Policies
* **Immutable Versions**: Workflow definitions are version-controlled (`v1`, `v2`, `v3`) and immutable.
* **Migration**: Active executions continue on their original version tag, preventing in-flight failures from schema changes.

---

## Target Performance Benchmarks
* **Workflow Scheduling**: < 50 ms
* **Worker Assignment Handshake**: < 20 ms
* **Checkpoint Save State**: < 50 ms
* **Parallel Sync Point Resolution**: < 20 ms
* **Workflow Crash Recovery**: < 5 seconds
