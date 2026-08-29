# Security Architecture (Part 2 — API Security, Data Protection, Encryption, Compliance & Secure Infrastructure)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the production security standards for the entire MindMesh platform. It establishes API threat mitigations, data classification, encryption parameters, secure file downloads, infrastructure hardening, and container configurations.

Every production deployment must comply with these standards.

---

## API Threat Protection & OWASP Compliance
MindMesh enforces strict runtime guards to prevent common network-level vulnerabilities:
* **SQL Injection**: Prevented by writing queries exclusively via the SQLAlchemy ORM and parameterized prepared statements. Raw string query concatenation is prohibited.
* **XSS Mitigations**: Escape dynamic HTML, sanitize rich text input, validate markdown formats, and restrict embedded inline styles.
* **Security Headers**: Applied by the reverse proxy (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy). CORS whitelist is strictly configured in production (no wildcard `*` allowed).
* **Rate Limiting**: Enforced on authentication endpoints, OTP creation, search triggers, and AI generation tasks.

---

## Data Classification & Encryption

### 1. Data Classification
* **Public**: General documentation, static logos, and assets.
* **Internal**: Product usage logs and configuration models.
* **Confidential**: Chat messages, files, vector context segments, and extracted summaries.
* **Highly Sensitive**: Refresh tokens, integration OAuth credentials, and database secrets.

### 2. Encryption Standards
* **In Transit**: TLS 1.3, HTTPS only. Insecure protocols are disabled.
* **At Rest**: Object storage nodes, database backups, and configuration files are encrypted.
* **Credential Hashing**: Password parameters (when added in future) utilize `Argon2id` or `bcrypt`. Plaintext hashing like MD5 is prohibited.

---

## Secure File Storage & Access
* Binary files reside outside PostgreSQL in dedicated object storage directories.
* **Access Control**: Public static access is disabled. Download access is gated via **Signed Download URLs** generated dynamically with a strict **10-minute expiration** window.

---

## Container & Infrastructure Security
* **Docker Hardening**: Production containers run as minimal base images using a **non-root user**. Filesystem is marked read-only where practical.
* **Backups & DR**:
  * Backup scope: PostgreSQL, ChromaDB indexes, object storage files, and logs.
  * **Recovery Point Objective (RPO)**: ≤ 15 minutes.
  * **Recovery Time Objective (RTO)**: ≤ 1 hour.
