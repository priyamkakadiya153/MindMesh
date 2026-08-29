# 04.2 — Codebase Organization

## Part 1 — Folder Structure, Module Organization, Feature Architecture, Naming Conventions & Source Code Layout

**Project:** MindMesh – AI-Powered Knowledge Intelligence Platform

**Phase:** 04 — Software Architecture & Codebase Documentation

**Document Version:** 1.0

**Document Type:** Codebase Organization Specification (COS)

**Status:** Draft

**Owner:** Software Architecture Team

---

# Purpose

This document defines how source code is organized throughout the MindMesh codebase.

While **04.1 Repository Architecture** defines the repository itself, this document specifies how every application, package, service, SDK, and feature should organize its source code.

It establishes:

* Enterprise Folder Structure
* Feature-Based Organization
* Module Architecture
* Source Code Layout
* Naming Standards
* Import Rules
* Layer Boundaries
* Package Organization
* Shared Code Strategy
* Source Code Governance

This document becomes the canonical guide for organizing all production code.

---

# Code Organization Philosophy

MindMesh code should be:

* Predictable
* Discoverable
* Modular
* Testable
* Maintainable
* Scalable
* Self-Documenting

A developer unfamiliar with the codebase should understand the structure within minutes.

---

# Organization Principles

Every source file should satisfy:

* One Responsibility
* One Owner
* One Module
* One Purpose

Avoid "miscellaneous" folders and ambiguous placement.

---

# Source Code Hierarchy

```text id="code-001"
Repository

↓

Application

↓

Feature

↓

Module

↓

Component

↓

Class

↓

Function
```

Each level has clearly defined responsibilities.

---

# High-Level Code Organization

```text id="code-002"
Application

↓

Business Features

↓

Shared Modules

↓

Infrastructure

↓

Platform

↓

Utilities
```

Business capabilities drive the organization.

---

# Feature-First Architecture

MindMesh follows a **Feature-First** approach.

Never organize by:

* Controllers
* Services
* Components
* Models

Instead organize by:

* Authentication
* Knowledge
* Search
* AI
* Files
* Workflows

Business capabilities own their implementation.

---

# Feature Structure

Every feature follows:

```text id="code-003"
feature/

├── api/
├── components/
├── hooks/
├── services/
├── store/
├── types/
├── schemas/
├── utils/
├── constants/
├── tests/
└── index.ts
```

Every feature is independently maintainable.

---

# Module Philosophy

A module represents one business capability.

Examples:

* Authentication
* Knowledge Base
* Search
* AI Chat
* Notifications
* Workflow Builder
* Administration

Modules should minimize coupling.

---

# Module Structure

```text id="code-004"
module/

├── domain/
├── application/
├── infrastructure/
├── presentation/
└── tests/
```

This structure mirrors Clean Architecture principles.

---

# Folder Standards

Each folder has a single purpose.

Avoid:

```text
helpers/

misc/

common/

temp/

new/
```

Folder names should describe business intent.

---

# Application Folder Structure

Example:

```text id="code-005"
web/

src/

app/

features/

layouts/

providers/

routes/

shared/

styles/

assets/

config/

tests/
```

Applications remain lightweight.

---

# Backend Service Structure

```text id="code-006"
service/

api/

domain/

application/

infrastructure/

workers/

events/

schemas/

tests/
```

Services expose only public APIs.

---

# AI Service Structure

```text id="code-007"
ai-runtime/

agents/

prompts/

retrieval/

memory/

evaluation/

tools/

models/

tests/
```

AI capabilities remain modular.

---

# Shared Package Structure

```text id="code-008"
package/

src/

tests/

docs/

examples/

README.md

CHANGELOG.md
```

Shared packages are independently publishable.

---

# Source Layout Standards

Each module contains:

* Source
* Tests
* Documentation
* Examples (if applicable)

Generated code remains isolated.

---

# Domain Organization

Domain code includes:

* Entities
* Value Objects
* Domain Services
* Business Rules
* Policies
* Events

Domain logic remains framework-independent.

---

# Application Layer

Responsible for:

* Use Cases
* Commands
* Queries
* Orchestration
* Transactions

Business workflows belong here.

---

# Infrastructure Layer

Responsible for:

* Database
* External APIs
* Search
* Storage
* AI Providers
* Queues

Infrastructure implements interfaces defined by the domain.

---

# Presentation Layer

Responsible for:

* REST API
* GraphQL
* WebSockets
* Frontend Components
* Controllers

Presentation never contains business rules.

---

# Naming Philosophy

Names should be:

* Descriptive
* Consistent
* Singular
* Domain-Oriented

Avoid abbreviations unless universally recognized.

---

# File Naming

Use:

```text id="code-009"
knowledge.service.ts

search.repository.ts

workflow.controller.py

notification.schema.ts
```

Prefer lowercase kebab-case for filenames.

---

# Folder Naming

Use:

```text id="code-010"
knowledge/

workflow/

notifications/

search/

authentication/
```

Folder names remain singular where appropriate.

---

# Class Naming

Examples:

```text id="code-011"
KnowledgeService

SearchEngine

WorkflowExecutor

UserRepository
```

Classes use PascalCase.

---

# Interface Naming

Examples:

```text id="code-012"
SearchRepository

KnowledgeStorage

EmbeddingProvider

NotificationChannel
```

Avoid prefixing interfaces with "I".

---

# Function Naming

Use verbs.

Examples:

```text id="code-013"
createWorkspace()

searchKnowledge()

generateSummary()

uploadDocument()
```

Functions express actions.

---

# Variable Naming

Use meaningful names.

Good:

```text id="code-014"
workspaceId

knowledgeChunk

embeddingVector

notificationQueue
```

Avoid generic names like:

* data
* obj
* temp
* value

---

# Constant Naming

Global constants:

```text id="code-015"
MAX_UPLOAD_SIZE

DEFAULT_TIMEOUT

CACHE_TTL
```

Use SCREAMING_SNAKE_CASE.

---

# Type Naming

Examples:

```text id="code-016"
User

Workspace

KnowledgeDocument

SearchResult
```

Types use PascalCase.

---

# Import Standards

Order imports:

```text id="code-017"
Standard Library

↓

Third-Party

↓

Internal Packages

↓

Relative Imports
```

Imports remain consistent.

---

# Import Rules

Prefer:

Absolute imports.

Avoid:

```text
../../../
```

Use aliases instead.

---

# Public API Pattern

Each module exposes:

```text id="code-018"
index.ts
```

Internal implementation remains hidden.

---

# Cross-Module Communication

Modules communicate through:

* Interfaces
* SDKs
* Events
* APIs

Never access another module's internals.

---

# Code Reuse

Reusable code belongs in:

* Shared Packages
* Platform Libraries
* SDKs

Copy-paste is prohibited.

---

# Test Organization

Every module contains:

```text id="code-019"
tests/

unit/

integration/

fixtures/
```

Tests remain close to implementation.

---

# Generated Code

Generated code belongs in:

```text id="code-020"
generated/
```

Never edit generated code manually.

---

# Configuration Organization

Configuration includes:

* Environment
* Feature Flags
* Constants
* Runtime Settings

Configuration remains externalized.

---

# Documentation Standards

Every module includes:

* README
* Architecture Notes
* Public API
* Examples

Documentation is version-controlled.

---

# Code Ownership

Every module defines:

* Owner
* Reviewers
* Maintainers
* Documentation Owner

Ownership prevents abandoned code.

---

# Architecture Boundaries

Boundaries enforced by CI:

* No circular imports
* No forbidden dependencies
* Layer validation
* Import validation

Architecture violations fail builds.

---

# Refactoring Guidelines

Refactor when:

* Duplication increases
* Complexity grows
* Naming becomes unclear
* Modules exceed responsibilities

Continuous improvement is encouraged.

---

# Code Review Standards

Review:

* Folder placement
* Naming
* Boundaries
* Dependencies
* Documentation
* Tests

Organization is part of quality.

---

# Deliverables

This document defines:

* Folder Structure
* Module Organization
* Feature Architecture
* Naming Conventions
* Source Layout
* Import Standards
* Layer Boundaries
* Shared Code Strategy
* Documentation Standards
* Code Governance

These standards govern how all MindMesh source code is organized.

---

# Dependencies

This document depends on:

* 04.0 — Software Architecture & Codebase Documentation
* 04.1 — Repository Architecture (Part 1 & Part 2)
* 03.7 — Backend Implementation Guide
* 03.8 — Frontend Implementation Guide

---

# Codebase Organization Status

The foundational code organization standards are now established.

They provide:

* Feature-First Organization
* Module Standards
* Source Layout
* Naming Conventions
* Layered Architecture
* Import Rules
* Code Ownership
* Governance

This document becomes the primary reference for organizing all source code within MindMesh.

---

# Next Document

## **04.2 — Codebase Organization (Part 2 — Layered Architecture, Dependency Rules, Module Communication, Code Boundaries, Design Principles & Maintainability Standards)**

The next document will define:

* Clean Architecture Implementation
* Layer Dependency Rules
* Module Communication Patterns
* Internal APIs
* Event-Driven Communication
* Code Boundary Enforcement
* Design Principles (SOLID, DRY, KISS, YAGNI)
* Maintainability Standards
* Technical Debt Guidelines
* Long-Term Evolution Strategy

This document completes the Codebase Organization specification by defining how code should interact, evolve, and remain maintainable throughout the lifecycle of MindMesh.
