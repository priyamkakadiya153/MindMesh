# High-Level Architecture — MindMesh Engineering Handbook

### Version 1.0

---

## Purpose
This document defines the overall software architecture of MindMesh. It establishes how the entire system is organized, how modules interact, and the architectural principles that every future implementation must follow.

---

## System Overview
MindMesh is an AI-Powered Knowledge Intelligence System designed to transform conversations, files, tasks, and decisions into structured, searchable, and actionable knowledge.

AI acts as a supporting intelligence layer that enhances communication by understanding, organizing, and retrieving knowledge. The architecture follows a modular layered approach to ensure maintainability, scalability, security, and ease of future expansion.

---

## Architectural Style
MindMesh follows the following architectural principles:
* Monolithic Modular Architecture (MVP)
* Feature-First Organization
* Clean Architecture
* Layered Architecture
* Domain-Driven Module Separation
* Service-Oriented Business Logic
* Repository Pattern
* Dependency Injection
* Event-Driven AI Processing (Background Tasks)

The MVP intentionally avoids microservices to reduce operational complexity while maintaining clear module boundaries for future scalability.

---

## Architectural Goals
The architecture has been designed to achieve the following objectives:
* Modular development
* Independent feature modules
* Easy testing
* High maintainability
* Secure communication
* AI independence
* Reusable components
* Future scalability
* Minimal technical debt

---

## System Layers

### 1. Presentation Layer
Responsible for user interaction.
* **Responsibilities**: User Interface, Forms, Navigation, Responsive Design, Client-side Validation, WebSocket Communication, State Management.
* *This layer never contains business logic.*

### 2. API Layer
Responsible for communication between frontend and backend.
* **Responsibilities**: REST APIs, Request Validation, Authentication, Authorization, Rate Limiting, Error Handling, API Documentation.
* *Business logic must never exist inside API routes.*

### 3. Service Layer
The core business layer.
* **Responsibilities**: Business Rules, Workflow Management, Feature Logic, Module Coordination, Transaction Management.
* *Every feature must have its own service.*

### 4. Repository Layer
Responsible for data access.
* **Responsibilities**: Database Queries, CRUD Operations, Filtering, Pagination, Transactions.
* *Repositories communicate only with databases. They never contain business logic.*

### 5. AI Intelligence Layer
The AI layer is completely independent.
* **Responsibilities**: Embedding Generation, Chunking, Retrieval, Semantic Search, Prompt Construction, Conversation Summarization, Task Extraction, Decision Extraction, Context Ranking.
* *If the AI service fails, the remaining platform must continue functioning normally.*

### 6. Data Layer
Responsible for persistent storage.
* **Includes**: PostgreSQL, Vector DB (ChromaDB / pgvector), Redis, Object Storage.

### 7. Infrastructure Layer
Responsible for deployment and platform services.
* **Responsibilities**: Docker, Environment Configuration, Logging, Monitoring, Background Jobs, File Storage, Security Configuration.

---

## Core Modules
MindMesh is organized into independent business modules. Each module owns its own APIs, services, repositories, and models:
* **Authentication**: User Registration, Mobile Number Verification, OTP, JWT, RBAC
* **Messaging**: Private Chat, Group Chat, Reactions, Read Receipts, Typing Indicators
* **Projects**: Project Creation, Members, Permissions
* **File Intelligence**: Upload, Download, Preview, Metadata Extraction, AI Understanding, External Application Support
* **Knowledge Intelligence**: Semantic Search, Knowledge Retrieval, AI Summary, Task Extraction, Decision Extraction
* **Search**: Keyword Search, Semantic Search, Hybrid Ranking
* **Notifications**: In-App Notifications, System Events
* **Administration**: User Management, Roles, Permissions, Audit Logs

---

## Data Flow
```
User -> Frontend -> REST API / WebSocket -> Authentication -> Business Service -> Repository -> Database -> AI Processing (asynchronous) -> Response
```
AI processing occurs asynchronously whenever possible to avoid blocking user interactions.

---

## Communication Strategy
* **REST APIs**: Used for Authentication, CRUD Operations, Search, Settings, Administration.
* **WebSockets**: Used for Messaging, Typing Indicators, Online Status, Read Receipts, Live Notifications.

---

## AI Processing Strategy
AI should never execute inside API routes unless immediate processing is required.
```
User Action -> Store Data -> Return Success Response -> Background Processing (Embedding Generation -> Vector Storage -> Knowledge Update)
```
This approach ensures low response latency.

---

## Module Independence
* Each business module must remain independent.
* Modules communicate through services instead of directly accessing each other's internal logic.
* Direct database access across modules is prohibited. This prevents tight coupling.

---

## Dependency Rules
Allowed Dependency Direction:
```
Frontend -> API -> Service -> Repository -> Database
```
* AI Services may be invoked only through the Service Layer.
* Repositories must never call AI services.
* Frontend must never communicate directly with databases.

---

## Scalability Strategy
The MVP follows a Modular Monolith architecture.
```
Modular Monolith -> Independent AI Services -> Independent Search Service -> Object Storage -> Distributed Deployment -> Microservices (if justified)
```

---

## High-Level Architecture Diagram
```
                           Users
                              │
                    React Web Application
                              │
                  REST API + WebSockets
                              │
                     Backend Application (FastAPI / Node.js)
                              │
     ┌───────────────┬───────────────┬───────────────┐
     │               │               │
Authentication   Messaging     Knowledge Intelligence
     │               │               │
     └───────────────┴───────────────┘
                     Service Layer
                              │
     ┌───────────────┬───────────────┬───────────────┐
     │               │               │
 PostgreSQL      Vector DB           Redis
     │           (pgvector / Chroma)
 Object Storage
```
