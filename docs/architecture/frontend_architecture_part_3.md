# Frontend Architecture (Part 3 — Frontend State Management, Routing & API Communication)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official frontend strategy for application state management, routing, API communication, caching, authentication flow, and real-time communication.

The objective is to ensure that all frontend modules communicate consistently with the backend while maintaining predictable application state and minimizing unnecessary re-renders.

---

## State Architecture Partitioning
We divide frontend state into four distinct areas:
1. **Server State (TanStack Query)**: Data retrieved from backend models (Users, messages, search, history). *Must never be duplicated inside Zustand.*
2. **Client State (Zustand)**: Temporary interface state (sidebar toggles, active room ID, modals, preferences). *Must never duplicate server data.*
3. **Form State (React Hook Form + Zod)**: Fields, input validation, and submit states.
4. **UI State (useState)**: Local, temporary UI toggles (dropdown focus, input state, menu hover).

---

## Query Key Standards
Query keys for TanStack Query must follow a predictable namespace:
* `["auth"]`
* `["users"]`
* `["conversations"]`
* `["conversation", conversation_id]`
* `["messages", conversation_id]`
* `["files"]`
* `["search", keyword]`
* `["notifications"]`
* `["dashboard"]`

---

## Zustand Store Organization
Global client stores must be split into single-responsibility stores located in `src/store/`:
* `auth.store.ts`
* `theme.store.ts`
* `sidebar.store.ts`
* `conversation.store.ts`
* `search.store.ts`
* `notification.store.ts`

*Constraint*: A single monolithic store file is prohibited.

---

## Routing and Auth Guards
* **Routing**: Managed via React Router, shallow endpoints matching domains (`/dashboard`, `/conversations`, `/files`, `/search`, `/settings`, `/profile`).
* **Route Guards**: Authentication validation and role token evaluation must execute before rendering protected templates. Unauthorized requests redirect immediately to public landing or login portals.

---

## API Communication & Axios Config
* **Axios Instance**: Exposes a centralized client (Base URL, default timeout, JWT authorization headers, interceptors for automatic access token refresh).
* **Service Layer**: Components communicate with API clients only through domain services (e.g. `auth.service.ts`, `conversation.service.ts`). *Axios must never be called directly inside component files.*

---

## WebSocket Client Manager
* WebSocket actions pass through a single centralized manager inside `src/lib/websocket.ts`.
* **Responsibilities**: Connection setups, reconnect protocols, heartbeats, message event dispatching, and subscription filters.
* *Constraint*: Single authenticated sessions must never bind multiple parallel WebSocket connections.
