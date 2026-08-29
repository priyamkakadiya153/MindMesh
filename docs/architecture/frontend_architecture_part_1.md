# Frontend Architecture (Part 1 — Frontend Design Principles & React Architecture)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the frontend architecture, engineering principles, and React development standards for MindMesh. The frontend delivers a modern, responsive, accessible, and high-performance user experience while maintaining a clean, scalable, and maintainable structure.

Every React component, page, hook, and service must follow the standards defined here.

---

## Frontend Philosophy
The frontend exists to deliver an intuitive and efficient user experience. It is **not** responsible for implementing business rules.

The frontend focuses on UI, UX, data presentation, user interaction, navigation, state synchronization, accessibility, and performance. Business logic always belongs to the backend.

---

## Core Design Principles
Every frontend feature must follow these principles:
* **Simplicity First**: Clear layouts, minimal noise.
* **Consistency**: Shared UI components and strict theme properties.
* **Reusability**: Shared React hooks, custom functions, and wrappers.
* **Accessibility**: Screen reader support, keyboard navigation, focus management.
* **Responsiveness**: Support for Desktop, Laptop, Tablet, and Mobile browser breakpoints.
* **Performance**: Optimized load times, code splitting, and memoization.
* **Type Safety**: Fully typed props, API interfaces, and state structures.
* **Separation of Concerns**: UI presentation is separate from API coordination.

---

## Smart vs Presentational Components
We categorize React components into two structures:

### 1. Smart Components (Containers)
* **Responsibilities**: Fetch data via TanStack Query, handle API services, manage client state interactions, and coordinate child presentation components.

### 2. Presentational Components (UI Elements)
* **Responsibilities**: Render the HTML elements, style data, and emit user interaction events back to smart parents.
* *Constraint*: Presentational components should remain stateless and logic-independent whenever possible.

---

## State Management Strategy

### 1. Server State (TanStack Query)
* Manages all transactional, dynamic server data (Conversations list, message history, files, query results).
* *Rule*: Server state must never be copied or synchronized into Zustand.

### 2. Client State (Zustand)
* Manages global UI preferences, theme selection (Dark/Light mode toggles), active room selections, and dialog visibility states.

### 3. Form State (React Hook Form + Zod)
* Manages input form validation, fields, and submit states.

### 4. Local Component State (useState)
* Manages temporary, isolated component states (e.g. isDropdownOpen, isHovered).

---

## API Communication Flow
Axios instances and REST calls are encapsulated in a dedicated service layer:
```text
React Component -> Service Layer (Axios instance wrapper) -> API Gateway -> Backend Database
```
* Component files must never call Axios or fetch utilities directly.

---

## Accessibility & Responsiveness Constraints
* MindMesh conforms to WCAG guidelines (aria-labels, semantic layout headers `main`/`section`/`nav`, color contrast).
* Mobile responsiveness is a requirement (supported breakpoints in CSS / Tailwind classes). A separate native mobile app is a non-goal for the MVP.
