# Security Architecture (Part 1 — Identity, Authentication, Authorization & Zero-Trust Security Model)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official security architecture of MindMesh. MindMesh follows a **Zero-Trust Security Model**, where no user, service, device, or request is trusted by default. Security is integrated into every layer of the application.

---

## Zero-Trust Request Pipeline
Every incoming API request is explicitly verified across all security gates:

```text
User Request -> Identity Verification -> JWT Validation -> RBAC Auth -> Ownership Checks -> Business Logic -> Response
```

* **Defense in depth**: Each application layer validates security contexts independently. No internal database or queue task is automatically trusted.
* **Least Privilege**: Users receive only the atomic permissions required to execute their specific action.

---

## Authentication Strategy (OTP + JWT)
Authentication is password-less, using mobile numbers and verified OTP codes.
* **OTP Issuance**: OTP requests are stored as secure hashes, automatically expire, enforce maximum retry thresholds, and are rate-limited. Plaintext OTPs must never be logged or saved.
* **Access Tokens**: Short-lived (15–30 minutes), stateless, cryptographically signed, carrying minimal identification claims.
* **Refresh Tokens**: Long-lived, rotated on usage, revocable, and persist via secure HttpOnly cookies to restrict client-side script access.

---

## Authorization & Permission Hierarchy
System permissions are atomic (e.g. `file.download`, `message.edit`) and inherit downward across system scopes:

```text
System Role (Global) -> Workspace Role -> Project Role -> Conversation Permission
```

* **Ownership Checks**: Resource ownership checks (e.g., verifying if the request author matches the message creator) occur independently of role evaluations.
* **Security Isolation**: Data residency boundaries across workspaces are strictly enforced. Chunks, messages, or files belonging to another workspace must never enter prompt contexts or search index retrieval pools.

---

## Sensitive Credentials Protection
* Database passwords, API credentials, and integration authorization tokens are stored encrypted using secure encryption configurations.
* Secret values (JWT keys, DB credentials) load exclusively from environment configurations. Hardcoding secrets in source files is prohibited.
* Security events (OTP failure, role change, session revocation) generate immutable audit logs.
