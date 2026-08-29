# 04.3 — Design Patterns & Architectural Patterns

## Part 2 — Repository, Unit of Work, Mediator, Observer, Decorator, Pipeline, Saga, Outbox, Circuit Breaker & Resilience Patterns

**Project:** MindMesh – AI-Powered Knowledge Intelligence Platform

**Phase:** 04 — Software Architecture & Codebase Documentation

**Document Version:** 1.0

**Document Type:** Architectural Pattern Specification (APS)

**Status:** Draft

**Owner:** Chief Software Architect

---

# Purpose

This document defines the implementation-level design patterns that every MindMesh service, module, AI component, workflow engine, and infrastructure component should follow.

While Part 1 defined enterprise architectural patterns, this document specifies the tactical patterns that engineers apply during implementation.

It establishes:

* Repository Pattern
* Unit of Work
* Mediator
* Observer
* Decorator
* Chain of Responsibility
* Pipeline
* Saga
* Transactional Outbox
* Circuit Breaker
* Retry
* Bulkhead
* Rate Limiter
* Idempotency
* Resilience Engineering

These patterns form the implementation standards for enterprise-grade software.

---

# Pattern Philosophy

Patterns should:

* Solve recurring problems
* Reduce complexity
* Improve maintainability
* Encourage consistency
* Increase resilience
* Support scalability

Patterns are applied deliberately—not mechanically.

---

# Pattern Hierarchy

```text id="pattern2-001"
Architectural Patterns

↓

Application Patterns

↓

Domain Patterns

↓

Infrastructure Patterns

↓

Resilience Patterns
```

Each pattern belongs to an appropriate layer.

---

# Repository Pattern

Repositories abstract persistence.

Applications interact with repositories rather than databases.

```text id="pattern2-002"
Application

↓

Repository Interface

↓

Infrastructure Implementation

↓

Database
```

---

# Repository Responsibilities

Repositories:

* Load Aggregates
* Save Aggregates
* Query Domain Objects
* Hide Storage Technology
* Enforce Persistence Contracts

Repositories never contain business logic.

---

# Repository Rules

Each aggregate has:

* One Repository Interface
* One Primary Implementation
* Clear Ownership

Avoid generic repositories.

---

# Unit of Work Pattern

Coordinates multiple repository operations into a single transaction.

```text id="pattern2-003"
Application Service

↓

Repositories

↓

Unit of Work

↓

Commit

↓

Database
```

---

# Unit of Work Responsibilities

* Begin Transaction
* Track Changes
* Commit
* Rollback
* Publish Events

Business logic does not manage transactions directly.

---

# Mediator Pattern

Modules communicate through a mediator instead of direct references.

```text id="pattern2-004"
Controller

↓

Mediator

↓

Command

↓

Handler
```

---

# Mediator Benefits

Provides:

* Loose Coupling
* Centralized Dispatch
* Easier Testing
* Clear Request Flow

Ideal for CQRS implementations.

---

# Command Pattern

Commands represent business actions.

Examples:

* CreateWorkspaceCommand
* UploadFileCommand
* GenerateSummaryCommand
* ExecuteWorkflowCommand

Commands modify state.

---

# Query Pattern

Queries retrieve information.

Examples:

* SearchKnowledgeQuery
* GetConversationQuery
* GetDashboardQuery

Queries never modify state.

---

# Observer Pattern

Observers react to published events.

```text id="pattern2-005"
Publisher

↓

Event

↓

Observers

↓

Handlers
```

---

# Observer Use Cases

Suitable for:

* Notifications
* Metrics
* Logging
* Search Indexing
* AI Processing
* Analytics

Observers should remain independent.

---

# Decorator Pattern

Decorators extend behavior without modifying existing code.

Examples:

* Caching
* Authorization
* Logging
* Rate Limiting
* Metrics
* Retry

Decorators are composable.

---

# Decorator Pipeline

```text id="pattern2-006"
Request

↓

Logging

↓

Authentication

↓

Authorization

↓

Caching

↓

Business Logic
```

Cross-cutting concerns remain separate.

---

# Chain of Responsibility

Each handler decides whether to process or pass the request.

Use for:

* Validation
* Authentication
* Middleware
* Workflow Rules

Handlers remain focused.

---

# Pipeline Pattern

A request passes through ordered processing stages.

```text id="pattern2-007"
Input

↓

Validation

↓

Authorization

↓

Business Logic

↓

Events

↓

Response
```

Pipelines simplify request processing.

---

# Strategy Pattern

Select algorithms dynamically.

Examples:

* AI Provider Selection
* Search Ranking
* Authentication Method
* Notification Channel

Behavior becomes configurable.

---

# Factory Pattern

Factories create complex objects.

Examples:

* AgentFactory
* WorkflowFactory
* ConnectorFactory
* PromptFactory

Construction logic remains centralized.

---

# Builder Pattern

Builders simplify complex object creation.

Examples:

* PromptBuilder
* SearchRequestBuilder
* WorkflowDefinitionBuilder

Builders improve readability.

---

# Adapter Pattern

Adapters integrate external systems.

Examples:

* Slack Adapter
* Google Drive Adapter
* GitHub Adapter
* Jira Adapter
* Outlook Adapter

External APIs remain isolated.

---

# Facade Pattern

Expose a simplified interface over complex subsystems.

Examples:

* AIFacade
* SearchFacade
* StorageFacade
* WorkflowFacade

Facades reduce implementation complexity.

---

# Proxy Pattern

Use proxies for:

* Lazy Loading
* Access Control
* Remote Services
* Monitoring

Clients remain unaware of implementation details.

---

# Saga Pattern

Coordinates distributed business transactions.

```text id="pattern2-008"
Step 1

↓

Step 2

↓

Step 3

↓

Complete
```

If a step fails, compensation begins.

---

# Saga Compensation

```text id="pattern2-009"
Failure

↓

Compensation

↓

Rollback Actions

↓

Consistent State
```

Distributed consistency is maintained.

---

# Saga Use Cases

Examples:

* Workspace Provisioning
* Subscription Activation
* Integration Setup
* AI Workflow Execution

Long-running workflows use sagas.

---

# Transactional Outbox Pattern

Guarantees reliable event publishing.

```text id="pattern2-010"
Database Transaction

↓

Outbox Table

↓

Background Publisher

↓

Message Bus
```

Events are never lost.

---

# Inbox Pattern

Prevents duplicate processing.

Responsibilities:

* Track Message IDs
* Ignore Duplicates
* Ensure Idempotency

Reliable consumers are mandatory.

---

# Circuit Breaker Pattern

Protects services from cascading failures.

States:

```text id="pattern2-011"
Closed

↓

Open

↓

Half-Open
```

Failed services recover safely.

---

# Retry Pattern

Retries transient failures.

Policies include:

* Fixed Delay
* Exponential Backoff
* Jitter
* Maximum Attempts

Retries are limited and observable.

---

# Bulkhead Pattern

Isolate workloads into separate resource pools.

Examples:

* AI Workers
* Search Workers
* File Processing
* Notifications

Failures remain contained.

---

# Timeout Pattern

Every remote operation defines:

* Connection Timeout
* Read Timeout
* Execution Timeout

Infinite waits are prohibited.

---

# Rate Limiter Pattern

Protects services from overload.

Supports:

* Token Bucket
* Leaky Bucket
* Sliding Window

Rate limits are configurable.

---

# Idempotency Pattern

Critical operations require idempotency.

Examples:

* Payments
* Workflow Execution
* AI Jobs
* File Upload Events

Duplicate requests produce the same result.

---

# Retry + Circuit Breaker Flow

```text id="pattern2-012"
Request

↓

Retry

↓

Circuit Breaker

↓

Fallback

↓

Response
```

Resilience is layered.

---

# Fallback Pattern

Fallbacks include:

* Cached Response
* Alternative Provider
* Graceful Degradation
* User Notification

Systems remain usable during failures.

---

# Resilience Engineering

Every critical service should support:

* Retry
* Timeout
* Circuit Breaker
* Bulkhead
* Health Checks
* Monitoring

Reliability is designed into the platform.

---

# Pattern Selection Matrix

| Problem                  | Pattern              |
| ------------------------ | -------------------- |
| Persistence              | Repository           |
| Transactions             | Unit of Work         |
| Request Dispatch         | Mediator             |
| Event Notification       | Observer             |
| Cross-Cutting Concerns   | Decorator            |
| Sequential Processing    | Pipeline             |
| Distributed Transactions | Saga                 |
| Reliable Messaging       | Transactional Outbox |
| External Failure         | Circuit Breaker      |
| Temporary Failure        | Retry                |
| Resource Isolation       | Bulkhead             |
| Request Throttling       | Rate Limiter         |

---

# Anti-Patterns

Avoid:

* God Repository
* Fat Service Classes
* Shared Mutable State
* Distributed Transactions without Compensation
* Infinite Retries
* Nested Decorators without Limits
* Synchronous Event Chains
* Tight Coupling Between Modules

---

# Pattern Governance

Every pattern implementation should include:

* Documentation
* Unit Tests
* Integration Tests
* ADR Reference
* Performance Review

Consistency is more important than novelty.

---

# Deliverables

This document defines:

* Repository Pattern
* Unit of Work
* Mediator
* Observer
* Decorator
* Pipeline
* Saga
* Transactional Outbox
* Circuit Breaker
* Retry
* Bulkhead
* Rate Limiter
* Idempotency
* Resilience Engineering

These standards govern the implementation of enterprise software patterns throughout MindMesh.

---

# Dependencies

This document depends on:

* 04.1 — Repository Architecture
* 04.2 — Codebase Organization
* 04.3 — Design Patterns & Architectural Patterns (Part 1)
* 03.7 — Backend Implementation Guide
* 03.9 — AI Implementation Guide

---

# Architectural Pattern Status

The Design Patterns & Architectural Patterns specification is now complete.

It establishes:

* Enterprise Architectural Patterns
* Tactical Design Patterns
* Messaging Patterns
* Reliability Patterns
* Distributed System Patterns
* Resilience Engineering Standards

This document serves as the implementation reference for software design across all MindMesh components.

---

# Next Document

## **04.4 — Shared Libraries & Internal SDK Architecture (Part 1 — Core Libraries, Shared Utilities, Common Types, Validation Framework & Platform SDKs)**

The next document will define:

* Shared Library Strategy
* Internal SDK Architecture
* Core Utilities
* Common Types
* Validation Framework
* Error Handling Library
* Configuration Library
* Logging SDK
* Authentication SDK
* Platform SDK Standards
* Package Publishing Guidelines

These standards establish the reusable software foundation that all MindMesh applications and services will build upon.
