# Repository Structure (Part 3 — Frontend Repository Structure)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official frontend repository structure for MindMesh. The frontend follows a **Domain-Driven, Feature-First Architecture** to ensure clean boundaries, high reusability, and isolation of business domains.

No new folders should be created without updating this document.

---

## Technology Stack
The Web Application utilizes the following technologies:
* **UI & Component Engine**: React (TypeScript), Vite, Tailwind CSS, Framer Motion, Lucide Icons.
* **Routing**: React Router.
* **Data Fetching & Server State**: TanStack Query (React Query) + Axios.
* **Client State**: Zustand.
* **Forms & Validation**: React Hook Form + Zod.

---

## Official Folder Structure

```text
apps/web/
├── public/                 # Static assets directly exposed to web server root
├── src/
│   ├── app/                # Application initialization, theme, query clients, global providers
│   ├── domains/            # Feature-first domain modules
│   │     ├── authentication/
│   │     ├── users/
│   │     ├── conversations/
│   │     ├── messages/
│   │     ├── files/
│   │     ├── knowledge/
│   │     ├── search/
│   │     ├── notifications/
│   │     ├── dashboard/
│   │     └── settings/
│   ├── shared/             # Reusable, pure UI components (ui/, modals/, forms/)
│   ├── layouts/            # Page shell layouts (DashboardLayout, AuthLayout)
│   ├── hooks/              # Reusable custom hooks (useDebounce, useWebSocket)
│   ├── services/           # Global client service instances
│   ├── providers/          # Global application providers
│   ├── assets/             # Images, fonts, and global animations
│   ├── styles/             # Global CSS files (globals.css, variables.css)
│   ├── types/              # Cross-domain global TypeScript types
│   ├── utils/              # Pure utility functions (date, string, file formatters)
│   ├── constants/          # Global route paths, API endpoints, configurations
│   ├── config/             # Runtime environment configuration
│   ├── routes/             # Client-side router configs
│   ├── lib/                # Wrappers around third-party libraries (axios, websocket)
│   │
│   ├── main.tsx            # Bootstrap entry point
│   └── App.tsx             # Main routing component
├── tests/                  # Frontend test suites
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.ts      # Tailwind CSS configuration
```

---

## Core Frontend Rules & Guidelines

### 1. Domain Isolation
* Every business domain owns its own sub-folders (e.g. `domains/conversations/components/`, `domains/conversations/services/`, etc.).
* Do not access internals of other domains directly. Communicate via common types or shared parameters.

### 2. State Partitioning
* **TanStack Query** is used for **Server State** (fetching, caching, mutation, loading indicators). Do not store server data inside Zustand.
* **Zustand** is used for **Client-side State** (sidebar collapsed, active room ID, modals visible).

### 3. Component Standards
* Components must satisfy the Single Responsibility Principle, be responsive, accessible, and typed.
* Components larger than **250 lines** must be refactored into smaller sub-components.

### 4. Dependency/Import Rules
* **Allowed**: Domain → Shared → Lib.
* **Prohibited**: Shared → Domain (Shared UI components must remain business-logic-independent).
* Always wrap third-party libraries inside the `src/lib/` folder (never import directly throughout the app).
