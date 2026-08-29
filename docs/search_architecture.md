# MindMesh Universal Search Engine - Architecture Documentation

## Overview
The MindMesh Universal Search Engine delivers enterprise-grade, permission-aware, unified search across all platform resources: Documents, Projects, Tasks, AI Conversations, Knowledge Base, Users, Workspaces, Organizations, Files, Notes, Meetings, Decisions, Workflows, Comments, Tags, and Collections.

---

## 1. Search Flow Diagram

```mermaid
flowchart TD
    User([User]) -->|Presses Cmd+K / Types Query| SearchUI[Universal Search Component UI]
    SearchUI -->|Debounced Request (~300ms)| API[GET /api/v1/search]
    API --> SearchService[SearchService Layer]
    SearchService --> OrgCheck{RBAC: Organization Member?}
    OrgCheck -- No --> Block[Return 0 Results]
    OrgCheck -- Yes --> WSCheck[Resolve Accessible Workspace IDs]
    WSCheck --> EngineAdapter[DatabaseSearchEngine Adapter]
    EngineAdapter --> DBIndex[(PostgreSQL search_index Table)]
    DBIndex --> Rank[Ranking Engine: Title Match + Keyword Frequency + Recency + Tags]
    Rank --> HistoryLog[(Log to search_history)]
    Rank --> Format[Format Facets, Snippets & Result Cards]
    Format --> ReturnResults[Return Json Response Envelope]
```

---

## 2. Database Schema

### `search_index`
| Column | Type | Index / Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Index record unique ID |
| `entity_type` | VARCHAR(50) | Indexed | Target entity type (e.g., `document`, `project`, `task`, `user`, `workflow`) |
| `entity_id` | UUID | Indexed | Target entity UUID in source table |
| `workspace_id` | UUID | Foreign Key (workspaces.id), Indexed | Workspace scope (NULL for org-wide) |
| `organization_id` | UUID | Foreign Key (organizations.id), Indexed | Tenant organization scope |
| `owner_id` | UUID | Foreign Key (users.id), Indexed | Resource creator/owner |
| `title` | VARCHAR(500) | Full Text / ILIKE | Entity title or primary display name |
| `content` | TEXT | Full Text / ILIKE | Entity body, description, or parsed text |
| `tags` | JSON | Indexed | List of tags associated with entity |
| `metadata_json` | JSON | GIN / JSON | Additional attributes (status, priority, file_type, size) |
| `created_at` | TIMESTAMP | Indexed | Entity creation timestamp |
| `updated_at` | TIMESTAMP | Indexed | Entity update timestamp |

### `search_history`
| Column | Type | Index / Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | History log item ID |
| `user_id` | UUID | Foreign Key (users.id), Indexed | User who executed search |
| `query` | VARCHAR(255) | Indexed | Search term executed |
| `created_at` | TIMESTAMP | Composite (user_id, created_at) | Timestamp of query execution |

---

## 3. Search Engine Adapter & Strategy Pattern

The architecture abstracts the search backend behind `BaseSearchEngine`:

```
               +----------------------+
               |   BaseSearchEngine   |  (Abstract Base Class)
               +----------------------+
                          |
         +----------------+----------------+
         |                                 |
+----------------------+        +--------------------+
| DatabaseSearchEngine |        | HybridSearchEngine | (Future Vector + RRF)
+----------------------+        +--------------------+
```

- **`DatabaseSearchEngine`**: Multi-column text search, exact title match boosting, recency decay weighting, RBAC workspace/org isolation.
- **`HybridSearchEngine`**: Ready for future vector embeddings (`pgvector`) & Reciprocal Rank Fusion without API breaking changes.

---

## 4. API Endpoints

- `GET /api/v1/search`: Universal search endpoint.
- `GET /api/v1/search/suggestions`: Real-time autocomplete suggestions (`q=inv`).
- `GET /api/v1/search/history`: Top 10 recent searches for authenticated user.
- `DELETE /api/v1/search/history`: Clears search history.

---

## 5. Performance & Security Features
1. **No SQL LIKE naive search**: Uses indexed `search_index` relational table with weighted scoring, facets, and pagination.
2. **Debouncing (~300ms)**: Eliminates unneeded frontend API requests during fast typing.
3. **RBAC Isolation**: Organization membership and workspace membership verified *before* returning queries.
4. **Auto-Indexing & Auto-Seeding**: Domain entities auto-index via `SearchIndexer` during updates and startup checks.
