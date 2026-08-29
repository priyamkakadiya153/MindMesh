# Database Architecture (Part 2.1 — Core Identity & RBAC)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the identity, authentication, and authorization database architecture for MindMesh. These tables form the foundation of the platform's security and session management.

---

## Identity & RBAC Table Schema Mapping

### 1. `users` Table (Primary Identity)
* **Purpose**: Primary register of active user identities.
* **Columns**:
  * `id`: UUID (PK, Version 7)
  * `mobile_number`: VARCHAR(20) (UNIQUE)
  * `country_code`: VARCHAR(5) (NOT NULL)
  * `is_mobile_verified`: BOOLEAN (DEFAULT FALSE)
  * `status`: UserStatus ENUM (e.g., `active`, `suspended`, `inactive`)
  * `last_login_at`: TIMESTAMP (NULL)
  * `created_at`: TIMESTAMP (NOT NULL)
  * `updated_at`: TIMESTAMP (NOT NULL)
  * `deleted_at`: TIMESTAMP (NULL)
* **Indexes**: `mobile_number` (UNIQUE), `status`, `created_at`

### 2. `user_profiles` Table (User Profiles)
* **Purpose**: Stores profile-related user metadata separately from the primary credentials.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `display_name`: VARCHAR (NOT NULL)
  * `username`: VARCHAR (UNIQUE, NULLABLE)
  * `bio`: TEXT (NULLABLE)
  * `profile_picture`: VARCHAR (NULLABLE)
  * `timezone`: VARCHAR (DEFAULT 'UTC')
  * `language`: VARCHAR (DEFAULT 'en')
  * `created_at`: TIMESTAMP, `updated_at`: TIMESTAMP

### 3. `user_preferences` Table (User Settings)
* **Purpose**: Stores application client-side configurations.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `settings`: JSONB (Stores layout settings, notification choices, search parameters)
  * `created_at`: TIMESTAMP, `updated_at`: TIMESTAMP

### 4. `devices` Table (Device Identifiers)
* **Purpose**: Identifies client browsers and systems logging in to enable session revocation and auditing.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `device_name`: VARCHAR
  * `device_type`: VARCHAR (e.g. `mobile`, `desktop`, `tablet`)
  * `platform`: VARCHAR
  * `browser`: VARCHAR
  * `ip_address`: VARCHAR
  * `last_active_at`: TIMESTAMP
  * `is_trusted`: BOOLEAN (DEFAULT FALSE)
  * `created_at`: TIMESTAMP

### 5. `otp_requests` Table (OTP Verifications)
* **Purpose**: Tracks OTP codes issued for mobile log-in verification.
* **Columns**:
  * `id`: UUID (PK)
  * `mobile_number`: VARCHAR(20) (NOT NULL)
  * `otp_hash`: VARCHAR(256) (NOT NULL - OTPs must be hashed, never stored in plaintext)
  * `expires_at`: TIMESTAMP (NOT NULL)
  * `attempt_count`: INT (DEFAULT 0)
  * `is_verified`: BOOLEAN (DEFAULT FALSE)
  * `created_at`: TIMESTAMP

### 6. `sessions` Table (Active Login Sessions)
* **Purpose**: Represents active login session mappings.
* **Columns**:
  * `id`: UUID (PK)
  * `user_id`: UUID (FK -> `users.id`, CASCADE)
  * `device_id`: UUID (FK -> `devices.id`, CASCADE)
  * `access_token_id`: VARCHAR (Trace token identifier)
  * `login_at`: TIMESTAMP (NOT NULL)
  * `last_activity_at`: TIMESTAMP (NOT NULL)
  * `expires_at`: TIMESTAMP (NOT NULL)
  * `revoked_at`: TIMESTAMP (NULL)

### 7. `refresh_tokens` Table (Session Slide Keys)
* **Purpose**: Tracks long-lived session sliding refresh keys.
* **Columns**:
  * `id`: UUID (PK)
  * `session_id`: UUID (FK -> `sessions.id`, CASCADE)
  * `token_hash`: VARCHAR(256) (NOT NULL - Tokens must be hashed before saving)
  * `expires_at`: TIMESTAMP (NOT NULL)
  * `revoked_at`: TIMESTAMP (NULL)
  * `created_at`: TIMESTAMP (NOT NULL)

---

## Authorization & RBAC Schema (Many-to-Many Mappings)

### 8. `roles` Table
* **Purpose**: Standard system access levels (e.g. `Admin`, `Member`, `Guest`).
* **Columns**: `id` (UUID PK), `name` (VARCHAR UNIQUE), `description` (VARCHAR), `created_at`, `updated_at`.

### 9. `permissions` Table
* **Purpose**: Atomic permissions (e.g. `message.send`, `conversation.delete`, `file.upload`).
* **Columns**: `id` (UUID PK), `name` (VARCHAR UNIQUE), `description` (VARCHAR), `created_at`, `updated_at`.

### 10. `role_permissions` Table
* **Purpose**: Junction mapping roles to atomic permissions.
* **Columns**: `id` (UUID PK), `role_id` (FK -> `roles.id`, CASCADE), `permission_id` (FK -> `permissions.id`, CASCADE), `created_at`.

### 11. `user_roles` Table
* **Purpose**: Binds users to specific roles.
* **Columns**: `id` (UUID PK), `user_id` (FK -> `users.id`, CASCADE), `role_id` (FK -> `roles.id`, RESTRICT), `assigned_by` (UUID FK -> `users.id`), `assigned_at` (TIMESTAMP).
