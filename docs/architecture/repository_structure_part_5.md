# Repository Structure (Part 5 — Shared Packages, Naming Conventions & Import Rules)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the shared packages architecture, global naming conventions, import strategy, dependency rules, and repository standards for MindMesh. It ensures that code remains reusable, predictable, and maintainable throughout the project's lifecycle.

---

## Shared Package Philosophy
Shared packages contain reusable code that can be consumed by multiple applications. If the same code is required by two or more applications, it belongs inside `packages/`. Packages must remain application-independent.

---

## Official Packages Layout

```text
packages/
├── ui/                 # Reusable frontend UI components (buttons, dialogs, cards)
├── types/              # Shared TypeScript type definitions (Users, Messages, APIs)
├── config/             # Shared configurations (theme constants, route lists, environment models)
├── utils/              # Pure, side-effect-free utility helper functions
└── eslint-config/      # Shared code linting configurations
```

No additional packages should be created unless they provide clear reuse across applications.

---

## Global Naming Conventions

### 1. Directories & Folders
All directory names must use **lowercase** and **kebab-case**:
* *Correct*: `user-profile`, `semantic-search`, `knowledge-engine`
* *Incorrect*: `UserProfile`, `TEMP`, `misc`

### 2. Files
* **Frontend**: **lowercase** and **kebab-case** (e.g. `message-card.tsx`, `search-panel.tsx`).
* **Backend (Python)**: **lowercase** and **snake_case** (e.g. `message_repository.py`, `search_schema.py`).

### 3. Components & Classes
Use **PascalCase**:
* *Components*: `ConversationList`, `SearchPanel`
* *Classes*: `MessageService`, `SearchRepository`

### 4. Functions
* **Frontend**: **camelCase** (e.g. `getMessages()`, `uploadFile()`).
* **Backend (Python)**: **snake_case** (e.g. `send_message()`, `extract_tasks()`).

### 5. Variables
* **Frontend/Backend**: descriptive and clean **snake_case** (e.g. `conversation_id`, `current_user`). Do not use abbreviation stubs (`data`, `temp`, `x`).

### 6. Constants & Environment Keys
Always use **UPPER_SNAKE_CASE**:
* *Constants*: `MAX_UPLOAD_SIZE`, `DEFAULT_PAGE_SIZE`
* *Environment Variables*: `DATABASE_URL`, `JWT_SECRET`

---

## Import Strategies & Ordering

### Dependency Rules
* Web → Packages (Allowed)
* API → Packages (Allowed)
* Packages → Web/API (Prohibited - points inward only)

### Import Ordering

#### Frontend
1. React Core
2. Third-party Libraries
3. Shared Packages (e.g. `@mindmesh/types`)
4. Internal Modules
5. Relative Imports
6. Stylesheets

#### Backend (Python)
1. Python Standard Library
2. Third-party packages (e.g. FastAPI, SQLModel)
3. Core Application systems (`app/core/`)
4. Shared utilities
5. Feature modules (`app/domains/`)
6. Local module relatives

---

## Code Organization & Limits
* **Components**: max ~250 lines
* **Services**: max ~300 lines
* **Repositories**: max ~250 lines
* Utility files should focus on a single responsibility. Files exceeding these limits should be evaluated for refactoring.
