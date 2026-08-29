# DevOps & Infrastructure Architecture (Part 1 — Development Environment, Docker, Networking & Infrastructure Design)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the complete infrastructure architecture for MindMesh. It establishes container specifications, networking boundaries, service discovery mappings, environment configs, health checks, and startup order parameters.

Every development and production deployment must comply with these standards.

---

## Containerized Services & Network Boundaries
MindMesh operates as a modular containerized stack. External requests hit Nginx, which routes them internally to frontend assets or backend endpoints:

```text
External Client -> HTTPS -> Nginx (Reverse Proxy)
                              │
       ┌──────────────────────┴──────────────────────┐
       ▼                                             ▼
Frontend Assets                              Backend Container
(Vite / React)                               (FastAPI App)
                                                     │
                             ┌───────────────────────┼───────────────────────┐
                             ▼                       ▼                       ▼
                        PostgreSQL                 Redis                 ChromaDB
                     (Structured DB)             (Cache/QS)            (Vector Index)
                             │                       │
                             ▼                       ▼
                       Object Storage        Background Worker
                       (MinIO / S3)             (AI/Embeds)
```

* **Network Isolation**: Backend, database, cache, vector index, and object storage nodes run on a private internal network, inaccessible directly from host networks.
* **Service Discovery**: Containers communicate using internal host service names (`postgres`, `redis`, `backend`, `worker`, `chromadb`, `minio`). Hardcoding internal IP addresses is prohibited.

---

## Port Mappings (Development Stack)
Standardized local ports used across the Docker Compose development stack:
* **React Web App**: `3000`
* **FastAPI Backend (REST / WS)**: `8000`
* **PostgreSQL Database**: `5432`
* **Redis Instance**: `6379`
* **MinIO Console/API**: `9000`
* **ChromaDB Vector Server**: `8001`

---

## Startup Order & Health Checks
Service dependencies mandate a strict container start-up order:

```text
PostgreSQL -> Redis -> ChromaDB -> MinIO -> Backend API -> Background Worker -> Web Frontend -> Nginx Proxy
```

* **Health checks**: Services (e.g. backend exposes `/health`) define explicit health check probes in Docker. Downstream containers wait for upstream health states to turn healthy before starting.
* **Statelessness**: Application containers remain completely stateless. All persistence is mapped to external Docker volumes.
