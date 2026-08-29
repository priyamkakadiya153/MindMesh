# Repository Structure (Part 1 — Repository Philosophy & Root Structure)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official repository structure of MindMesh. Every future feature, module, package, configuration, documentation, and deployment asset must follow this document.

No developer or AI assistant is allowed to create arbitrary folders or reorganize the repository without updating this document.

---

## Repository Philosophy
MindMesh follows a **Production-Grade Modular Monorepo Architecture**.

The repository is designed for:
* Maintainability
* Scalability
* Clean Architecture
* Feature Isolation
* Reusability
* Independent Modules
* Future Team Collaboration

The repository is **NOT** a collection of frontend and backend folders. It represents the entire product.

---

## Why Monorepo?
Managing all parts of the project inside one repository provides:
* Single source of truth
* Shared versioning
* Easier dependency management
* Easier deployment
* Easier documentation
* Consistent architecture
* Better code reuse

---

## Repository Principles
1. **One repository. One product.** Never split the project into multiple Git repositories during MVP development.
2. **Everything has one place.** Every file should have exactly one logical location. Duplicate folders are prohibited.
3. **Feature ownership.** Every business domain owns its own implementation. Never scatter files across unrelated folders.
4. **Shared code belongs inside packages.** Never duplicate utility functions, types, or UI components.
5. **Infrastructure is separate.** Infrastructure code must never mix with application code.
6. **Documentation is part of the repository.** Architecture documentation must live beside the source code.

---

## Repository Layout
The root directory must contain only the following high-level folders:

```
mindmesh/
├── apps/                 # Executable applications (e.g. Web, API)
├── packages/             # Reusable code shared across applications (e.g. Types, UI library)
├── infrastructure/       # Deployment, proxy, and monitoring configs
├── docker/               # Dockerfiles and development containers
├── docs/                 # Engineering docs and designs
├── scripts/              # Database initialization and build utilities
├── .github/              # Github Action workflows and PR templates
│
├── .env.example          # Environment variables template
├── .gitignore            # Version control exclusions
├── docker-compose.yml    # Development environment runner
├── README.md             # Developer entry point
├── LICENSE               # Licensing terms
└── Makefile              # Development task runner
```

No additional root folders should be introduced unless approved by the architecture documentation.

---

## Repository Rules
* Never place business logic in the repository root.
* Never create miscellaneous folders.
* Never store generated files inside source folders.
* Never mix documentation with implementation.
* Never duplicate configuration files.
* Never create temporary folders inside the repository.

---

## Folder Naming Standards
All folder names must use **lowercase**, **kebab-case**, and **descriptive names**.
* **Good**: `user-profile`, `semantic-search`, `knowledge-engine`
* **Bad**: `Temp`, `misc`, `new`, `demo`, `test2`, `final`, `latest`
