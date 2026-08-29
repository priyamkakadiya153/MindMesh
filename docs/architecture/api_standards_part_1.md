# API Standards & SDK Architecture (Part 1 — API Design Principles, REST Standards, Versioning & SDK Guidelines)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official API Architecture for MindMesh. It establishes design principles, resource routing naming, payload validation standards, response formatting, cursor pagination schemas, version policies, and SDK development guidelines.

Every REST controller, endpoint, and model contract must comply with this document.

---

## API Philosophy & Routing
MindMesh endpoints model business capabilities rather than direct database layouts:
* **Versioning**: All routes prefix URL versions (e.g. `/api/v1/workspaces`).
* **Resource Naming**: Plural lowercase nouns separated by hyphens (e.g. `/project-members`, `/search-results`). verbiage in routes is prohibited.
* **Controller Isolation**: Routers receive and validate payloads (using Pydantic models) and delegate processing to the Service layer.

---

## Request & Response Standards

### 1. Request Header Contexts
Common headers verified on requests: `Authorization: Bearer <JWT>`, `Content-Type`, `X-Request-ID`, `X-Client-Version`.

### 2. Standard Success Format
```json
{
  "success": true,
  "message": "Resource action succeeded.",
  "data": { ... },
  "meta": { ... }
}
```

### 3. Standard Error Format
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Required parameters are missing.",
    "details": []
  },
  "request_id": "req-12345"
}
```

### 4. Cursor Pagination Schema
Cursor-based pagination is preferred over offsets to guarantee large lists performance:
* **Request**: `?cursor=<hash_id>&limit=20`
* **Response**:
```json
{
  "data": [ ... ],
  "pagination": {
    "next_cursor": "abc123next",
    "has_more": true
  }
}
```

---

## OpenAPI Standards & Client SDKs
* **OpenAPI 3.1**: Swagger UI and ReDoc pages are generated automatically by FastAPI, documenting endpoint parameter types, schemas, and security requirements.
* **Auto-generated SDKs**: Client SDK packages (TypeScript and Python) are built automatically from the compiled OpenAPI JSON specs, ensuring type-safe wrappers.
