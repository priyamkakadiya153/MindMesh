# Backend Architecture (Part 3 — API Design, Middleware, Authentication & Authorization)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official API architecture, middleware pipeline, authentication system, authorization model, request/response standards, and security policies for MindMesh.

Every endpoint, middleware, and authentication flow must comply with this document.

---

## API Design & Resource Naming
* **Versioning**: All endpoint routes are versioned under `/api/v1/` (e.g. `/api/v1/conversations`, `/api/v1/messages`).
* **Resource Naming**: Plural nouns only (e.g. `/users`, `/files`, `/notifications`).
* **Method Semantics**: `GET` (retrieve), `POST` (create), `PUT` (replace), `PATCH` (partial updates), `DELETE` (soft deletes).

---

## Standardized JSON Formats

### 1. Success Response
```json
{
  "success": true,
  "message": "Resource processed successfully.",
  "data": { ... },
  "meta": { ... }
}
```

### 2. Error Response
```json
{
  "success": false,
  "message": "Action not allowed.",
  "error": {
    "code": "FORBIDDEN"
  }
}
```

### 3. Pagination Standard
* **Parameters**: `?page=1&page_size=20`
* **Response Meta**:
```json
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 120,
    "total_pages": 6
  }
}
```

---

## Middleware Execution Pipeline Order
Requests are intercepted sequentially in this mandatory order:
1. **Request ID Injection**
2. **Request Logging**
3. **CORS Headers**
4. **Security Headers**
5. **Rate Limiting**
6. **Authentication JWT Parsing**
7. **Authorization Guards (RBAC)**
8. **Pydantic Validation Schemas**
9. **API Route Controller Execution**

---

## Authentication & JWT Strategy
MindMesh utilizes **Mobile Number + OTP Authentication** (passwords are a non-goal for the MVP).
* **Access Token**: Short-lived (15–30 minutes) for API authentication.
* **Refresh Token**: Long-lived for session sliding, secure HttpOnly cookie persistence.
* **Role-Based Access Control (RBAC)**: Supports roles `Admin`, `Member`, and `Guest` enforced using dependencies in routing and checking permissions inside the Service layer.
* **Standardized Error Codes**: `INVALID_OTP`, `UNAUTHORIZED`, `FORBIDDEN`, `RESOURCE_NOT_FOUND`, `VALIDATION_ERROR`, `FILE_TOO_LARGE`, `RATE_LIMIT_EXCEEDED`.
