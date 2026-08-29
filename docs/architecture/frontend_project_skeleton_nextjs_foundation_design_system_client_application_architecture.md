# 20.2 — Frontend Project Skeleton, Next.js Foundation, Design System & Client Application Architecture

**Project:** MindMesh – AI-Powered Knowledge Intelligence Platform

**Phase:** Phase 20 — Enterprise Implementation Blueprint & Production Development

**Document Version:** 1.0

**Document Type:** Frontend Foundation Implementation Guide

**Status:** Production Implementation Blueprint

**Classification:** Frontend Engineering Guide

**Architecture Authority:** Platform Engineering

**Owners:**

* Chief Technology Officer
* Frontend Engineering Team
* Platform Engineering Team
* UI/UX Design Team
* Core Platform Team

---

# Purpose

This document defines the frontend foundation of MindMesh.

It establishes the Next.js application architecture, routing, layouts, design system, UI components, authentication flow, state management, API integration, theming, and frontend development standards.

This is the implementation guide for the complete frontend.

---

# Technology Stack

| Layer | Technology |
|--------|------------|
| Framework | Next.js 15 |
| Language | TypeScript |
| UI | React 19 |
| Styling | Tailwind CSS |
| Components | shadcn/ui |
| Icons | Lucide React |
| State | Zustand |
| Server State | TanStack Query |
| Forms | React Hook Form |
| Validation | Zod |
| Charts | Recharts |
| Tables | TanStack Table |
| Authentication | JWT |
| Theme | next-themes |

---

# Frontend Architecture

```text
Browser
    │
    ▼
Next.js App Router
    │
    ▼
Layouts
    │
    ▼
Pages
    │
    ▼
Components
    │
    ▼
API Layer
    │
    ▼
FastAPI Backend
```

---

# Folder Structure

```text
frontend/web/
├── src/
│   ├── app/
│   ├── components/
│   │   ├── ui/
│   │   ├── common/
│   │   ├── navigation/
│   │   ├── forms/
│   │   ├── tables/
│   │   ├── cards/
│   │   ├── dialogs/
│   │   ├── charts/
│   │   ├── feedback/
│   │   └── layout/
│   ├── features/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── projects/
│   │   ├── documents/
│   │   ├── chat/
│   │   ├── search/
│   │   ├── agents/
│   │   ├── analytics/
│   │   └── settings/
│   ├── layouts/
│   ├── hooks/
│   ├── lib/
│   ├── services/
│   ├── store/
│   ├── styles/
│   ├── types/
│   ├── utils/
│   ├── providers/
│   ├── middleware/
│   ├── assets/
│   └── constants/
```

---

# App Router

```text
app/
├── (layout)/
├── dashboard/
├── projects/
├── workspace/
├── documents/
├── search/
├── chat/
├── agents/
├── analytics/
├── settings/
├── login/
├── register/
└── api/
```

---

# Layout Hierarchy

```text
RootLayout
↓
AuthLayout
↓
DashboardLayout
↓
Feature Layout
↓
Page
↓
Components
```

---

# UI Components

```text
components/
├── ui/
├── common/
├── navigation/
├── forms/
├── tables/
├── cards/
├── dialogs/
├── charts/
├── feedback/
└── layout/
```

---

# Feature Modules

```text
features/
├── auth/
├── dashboard/
├── projects/
├── documents/
├── chat/
├── search/
├── agents/
├── analytics/
└── settings/
```

Each feature contains:

```text
components/
hooks/
services/
types/
store/
```

---

# State Management

### Global State

* Authentication
* User
* Organization
* Theme
* Sidebar
* Notifications

Managed with: **Zustand**

### Server State

* Users
* Projects
* Documents
* Search
* Chat
* Analytics

Managed with: **TanStack Query**

---

# API Layer

```text
services/
├── auth.ts
├── users.ts
├── projects.ts
├── documents.ts
├── chat.ts
├── search.ts
└── analytics.ts
```

Every backend module has one frontend service.

---

# Authentication Flow

```text
Login
↓
JWT Token
↓
Store Session
↓
Protected Routes
↓
Auto Refresh Token
↓
Logout
```

---

# Theme System

Support:

* Light
* Dark
* System

Use: **next-themes**

---

# Design System

### Colors

* Primary
* Secondary
* Success
* Warning
* Error
* Neutral

### Typography

* Heading
* Title
* Body
* Caption

### Spacing

* 4px Grid

### Radius

* Standard

### Icons

* Lucide

---

# Navigation

### Sidebar

* Dashboard
* Projects
* Workspace
* Documents
* Search
* Chat
* AI Agents
* Analytics
* Settings

### Top Navigation

* Search
* Notifications
* Profile
* Organization Switcher

---

# Dashboard Widgets

* Recent Activity
* AI Insights
* Documents
* Tasks
* Analytics
* Search
* Notifications
* Team Members

---

# Forms

Use:

* React Hook Form
* Zod Validation

Every form supports:

* Validation
* Loading State
* Error State
* Success State

---

# Error Handling

```text
Loading
↓
Success
↓
Empty
↓
Error
↓
Retry
```

Every page follows this pattern.

---

# Responsive Breakpoints

| Device | Width |
|----------|-------|
| Mobile | < 768px |
| Tablet | 768px |
| Laptop | 1024px |
| Desktop | 1280px |
| Large | 1536px |

---

# Performance

Enable:

* Lazy Loading
* Dynamic Imports
* Image Optimization
* Code Splitting
* Route Prefetching
* Suspense
* Streaming

---

# Accessibility

Support:

* Keyboard Navigation
* Screen Readers
* ARIA Labels
* Focus Management
* Color Contrast
* Semantic HTML

---

# Testing

Frontend includes:

* Unit Tests
* Component Tests
* Integration Tests
* E2E Tests

Tools:

* Vitest
* Playwright

---

# Coding Standards

Use:

* Functional Components
* TypeScript
* Custom Hooks
* Feature Modules
* Reusable Components

Avoid:

* Large Components
* Inline Styles
* Business Logic in UI
* Duplicate Components

---

# Deliverables

This document defines:

* Next.js Foundation
* Folder Structure
* Routing
* Layouts
* Design System
* UI Components
* State Management
* API Integration
* Authentication
* Responsive Design
* Testing Standards

---

# Relationship to Previous Architecture

This architecture extends:

* **Phase 20.1 (Backend Project Skeleton)**: [backend_project_skeleton_fastapi_foundation_core_service_architecture.md](file:///d:/7%20sem/MindMesh/docs/architecture/backend_project_skeleton_fastapi_foundation_core_service_architecture.md)
* **Phase 20.0 (Monorepo Setup)**: [monorepo_setup_repository_initialization.md](file:///d:/7%20sem/MindMesh/docs/architecture/monorepo_setup_repository_initialization.md)
* **Phase 17.8 (Customer Experience Platform)**: [customer_experience_platform_community_ecosystem_learning_academy_developer_experience_enterprise_engagement_platform.md](file:///d:/7%20sem/MindMesh/docs/architecture/customer_experience_platform_community_ecosystem_learning_academy_developer_experience_enterprise_engagement_platform.md)

---

# Next Document

## **20.3 — Enterprise Database Architecture, PostgreSQL Schema, Alembic Migrations & Data Layer Implementation**

The next document defines the enterprise database implementation, including physical PostgreSQL database schemas, indexes, partition policies, Alembic migration structures, base repository classes, and transaction management abstractions.

Link: [enterprise_database_architecture_postgresql_schema_alembic_migrations_data_layer_implementation.md](file:///d:/7%20sem/MindMesh/docs/architecture/enterprise_database_architecture_postgresql_schema_alembic_migrations_data_layer_implementation.md)
