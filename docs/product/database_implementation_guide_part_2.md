# 03.6 — Database Implementation Guide

## Part 2 — Table Implementation Specifications, Entity Migrations, Seed Data, Views, Functions, Triggers & Stored Procedures

**Document Version:** 1.0

**Project:** MindMesh – An AI-Powered Knowledge Intelligence System

**Document Type:** Database Implementation Guide (DIG)

**Status:** Draft

**Owner:** Database Engineering Team

---

# Purpose

This document defines how every database object inside MindMesh is implemented.

While Part 1 defined migration standards, this document defines:
* Table Implementation Standards
* Entity Migration Strategy
* Seed Data
* Views
* Materialized Views
* Functions
* Triggers
* Stored Procedures
* Generated Columns
* Row-Level Security
* Database Performance Objects

Every database object must comply with these standards.

---

# Database Implementation Philosophy

The database is not merely storage.

It is responsible for:
* Maintaining integrity
* Enforcing constraints
* Providing optimized queries
* Supporting security
* Enabling analytics
* Preserving audit history

Business logic belongs in services, but data integrity belongs in the database.

---

# Entity Implementation Order

Database entities are implemented in dependency order.

```text
Identity

↓

Organizations

↓

Users

↓

RBAC

↓

Workspaces

↓

Projects

↓

Conversations

↓

Messages

↓

Files

↓

Knowledge

↓

AI

↓

Workflow

↓

Analytics

↓

Administration
```

---

# Table Implementation Standards

Every table must define:
* Table Name
* Primary Key
* Foreign Keys
* Constraints
* Indexes
* Audit Columns
* Soft Delete Policy
* Partition Strategy (if applicable)

---

# Standard Table Template

Every table follows:

```text
Table

↓

Columns

↓

Constraints

↓

Indexes

↓

Triggers

↓

Policies

↓

Comments
```

Database comments are mandatory.

---

# Common Columns

Every business table includes:

```text
id

created_at

updated_at

created_by

updated_by

deleted_at (optional)
```

Optional:
```text
version

status

metadata
```

---

# UUID Strategy

All entities use UUID v7 (preferred) or UUID v4 if v7 is unavailable.

Reasons:
* Globally unique
* Better distributed systems support
* Safer external identifiers

Auto-increment IDs are avoided.

---

# Entity Migration Strategy

Each entity receives its own migration.

Example:

```text
V0001_users

V0002_roles

V0003_permissions

V0004_workspaces

V0005_projects
```

Never mix unrelated entities in one migration.

---

# Reference Data

Reference tables include:
* Roles
* Permissions
* Languages
* Countries
* Themes
* Notification Types
* Workflow Statuses
* AI Providers

These are seeded automatically.

---

# Seed Data Strategy

Seed data is divided into:

```text
System Seed

↓

Development Seed

↓

Demo Seed

↓

Test Seed
```

Production only contains System Seed.

---

# System Seed

Includes:
* Default Roles
* Permission Matrix
* Default Organization Settings
* Feature Flags
* AI Prompt Templates
* Workflow Templates

---

# Development Seed

Provides:
* Sample Users
* Demo Workspaces
* Demo Projects
* Example Knowledge
* AI Test Data

Never deployed to production.

---

# Table Categories

MindMesh tables fall into six categories.

```text
Master Data

Transactional

Relationship

Event

Analytics

Configuration
```

Each category has different optimization rules.

---

# Master Data Tables

Examples:
* users
* organizations
* roles
* permissions
* workspaces

Highly normalized.

---

# Transaction Tables

Examples:
* messages
* files
* knowledge_articles
* workflow_runs

Optimized for writes.

---

# Relationship Tables

Examples:
* workspace_members
* project_members
* role_permissions

Composite unique constraints are required.

---

# Event Tables

Examples:
* activity_logs
* audit_logs
* ai_requests
* notifications

Partitioned by date.

---

# Analytics Tables

Examples:
* usage_metrics
* search_metrics
* ai_metrics

Optimized for reporting.

---

# Configuration Tables

Examples:
* settings
* integrations
* themes

Frequently read, rarely updated.

---

# Database Views

Views simplify common queries.

Examples:

```text
active_users_view

workspace_summary_view

project_dashboard_view

knowledge_statistics_view

organization_health_view
```

Views never contain business logic.

---

# Materialized Views

Use for expensive calculations.

Examples:
* Search Statistics
* Knowledge Metrics
* AI Usage
* Executive Dashboard
* Organization Health

Refresh asynchronously.

---

# SQL Functions

Functions perform reusable calculations.

Examples:

```text
calculate_workspace_storage()

calculate_ai_usage()

calculate_health_score()

normalize_search_query()
```

Functions remain deterministic where possible.

---

# Stored Procedures

Use only for:
* Bulk Imports
* Batch Processing
* Large Maintenance Tasks
* Scheduled Cleanup
* Historical Data Migration

Avoid placing application business logic inside stored procedures.

---

# Trigger Standards

Triggers should be minimal.

Recommended uses:
* updated_at maintenance
* Audit logging
* Version increment
* Search index queue
* Cache invalidation events

Avoid complex trigger chains.

---

# Generated Columns

Use generated columns for:
* Search normalization
* File extensions
* Full names
* Computed identifiers

Avoid duplicating application logic.

---

# Row-Level Security (RLS)

Enable RLS for multi-tenant tables.

Policies include:
* Organization isolation
* Workspace isolation
* User ownership
* Role-based visibility

Every policy is tested.

---

# Multi-Tenant Isolation

Every tenant-scoped table contains:

```text
organization_id

workspace_id
```

Queries never bypass tenant filtering.

---

# Foreign Key Standards

Foreign keys should:
* Reference UUIDs
* Use indexed columns
* Restrict unsafe deletion
* Cascade updates only when appropriate

---

# Index Strategy

Each table includes:
Primary Index

↓

Foreign Key Index

↓

Search Index

↓

Composite Index

↓

Partial Index (if required)

Indexes are reviewed regularly.

---

# Partial Indexes

Use for:
* Active Records
* Pending Workflows
* Unread Notifications
* Recent Activity

Reduces index size.

---

# Expression Indexes

Examples:
* LOWER(email)
* LOWER(slug)
* Search vectors
* Normalized titles

Optimize frequent queries.

---

# Full-Text Search Objects

Create search vectors for:
* Knowledge
* Messages
* Files
* Documentation
* Projects

Hybrid retrieval combines these with embeddings.

---

# JSONB Standards

Allowed for:
* Dynamic Configuration
* Integration Payloads
* AI Metadata
* User Preferences

Avoid relational modeling inside JSONB.

---

# Audit Logging

Every critical modification records:
* Actor
* Action
* Entity
* Previous Value
* New Value
* Timestamp
* IP Address (if available)
* Correlation ID

Audit history is immutable.

---

# Data Retention

Retention policies:

| Data Type | Policy |
| --- | --- |
| Audit Logs | Long-term retention |
| Activity Logs | Configurable retention |
| AI Requests | Configurable retention |
| Notifications | Automatic archival |
| Sessions | Automatic expiration |

Retention is organization-configurable where applicable.

---

# Archive Strategy

Archived data is:
* Read-only
* Searchable (optional)
* Compressed
* Restorable

Archival reduces operational database size.

---

# Database Performance Standards

Every table must define:
* Expected Row Count
* Growth Rate
* Index Strategy
* Query Pattern
* Archival Policy
* Partition Strategy

Performance planning begins before deployment.

---

# Migration Testing

Every migration validates:
* Forward Migration
* Rollback
* Constraints
* Data Integrity
* Index Creation
* Performance
* Seed Compatibility

Migration tests are automated.

---

# Production Deployment Strategy

Deployment process:

```text
Backup

↓

Migration

↓

Integrity Validation

↓

Performance Check

↓

Application Verification

↓

Monitoring
```

Production deployment includes rollback readiness.

---

# Database Documentation

Each entity includes:
* Purpose
* Relationships
* Constraints
* Indexes
* Migration History
* Performance Notes
* Ownership

Documentation remains synchronized with implementation.

---

# Governance Checklist

Before approval:
* Naming compliant
* Constraints reviewed
* Indexes optimized
* Seed data validated
* Functions reviewed
* Triggers reviewed
* Performance verified
* Documentation updated

No database object enters production without review.

---

# Deliverables

This document defines:
* Table Implementation Standards
* Entity Migration Strategy
* Seed Data Standards
* Views
* Materialized Views
* SQL Functions
* Stored Procedures
* Triggers
* Generated Columns
* Row-Level Security
* Database Governance

These standards govern the implementation of every database object in MindMesh.

---

# Dependencies

This document depends on:
* 02.2.5 — Database Architecture (All Parts)
* 03.1 — Product Requirements Document
* 03.3 — Feature Specifications
* 03.6 — Database Implementation Guide (Part 1)

---

# Database Implementation Status

The Database Implementation framework is now complete.

It defines:
* Migration Strategy
* Entity Implementation
* Database Objects
* Performance Standards
* Security Policies
* Governance
* Operational Procedures

This becomes the implementation reference for all database development.
