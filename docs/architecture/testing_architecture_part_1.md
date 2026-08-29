# Testing Architecture (Part 1 — Testing Strategy, Quality Assurance, Test Pyramid & Automation Framework)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official Testing Architecture for MindMesh. It establishes quality assurance principles, unit testing setups, integration targets, API/database validations, AI evaluations, E2E flows, and coverage metrics.

Every feature must satisfy this document before it is marked complete.

---

## Testing Pyramid & Ratios
MindMesh adheres to a standard test distribution ratio:

```text
E2E Tests (10%) -> Integration Tests (20%) -> Unit Tests (70%)
```

* **Unit Tests (70%)**: Fast, isolated execution validating specific services, repositories, validators, and hooks.
* **Integration Tests (20%)**: Exercises linked service interactions (e.g. backend to PostgreSQL, Redis, or ChromaDB). Mocks are restricted to external API integrations.
* **End-to-End Tests (10%)**: Playwright tests executing critical user workflows.

---

## Frameworks & Tooling

### 1. Backend Testing
* **Framework**: `pytest`.
* **Coverage Target**: Minimum **85%** (95% for critical auth, security, and parsing modules).
* **Scopes**: Repositories, domain services, validator utility functions.

### 2. Frontend Testing
* **Framework**: `Vitest` + `React Testing Library`.
* **Coverage Target**: Minimum **80%**.
* **Scopes**: Individual components, custom hooks, helper utilities, and form schema validators.

### 3. E2E User Journeys
* **Framework**: `Playwright`.
* **Scopes**: OTP verification loops, workspace builders, conversation creations, file uploads, and search queries.

---

## AI & Retrieval Engine Testing
AI modules require behavioral and qualitative evaluation tests:
* **Retrieval Quality**: Assesses chunk index matching, ranking outputs, and permission metadata filters (ensuring no vector chunks are retrieved from unauthorized workspaces).
* **Citation Verification**: Verifies that LLM answers trace correctly to database message IDs or object storage paths.
* **Prompt Integrity**: Assesses context token boundaries, dynamic templates rendering, and citation rules compliance.

---

## CI Quality Gates & Checks
Pull requests are blocked from merging to `develop` or `main` if any QA check fails:
1. **Lint/Formatting Check**: ESLint (Frontend) and Ruff/Black (Backend).
2. **Type check**: TypeScript compiler (TSC).
3. **Automated Test Run**: Passing backend pytest and frontend Vitest suites.
4. **Security Vulnerability Scan**.
5. **Code Coverage Gates** met.
