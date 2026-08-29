# Knowledge Graph Architecture (Part 1 — Knowledge Graph Data Model, Entity Extraction, Relationship Modeling & Organizational Memory)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the Knowledge Graph Architecture of MindMesh. The Knowledge Graph tracks how information is connected across rooms, files, tasks, and users. It details node structures, directional edge categories, entity resolution pipelines, and graph queries.

---

## Graph Model (Nodes & Edges)

### 1. Node Categories
The graph models collaborative items as distinct nodes:
* `Workspace`, `Project`, `Conversation`, `Message`, `Document`, `File`, `Task`, `Decision`, `User`, `Meeting`, `Topic`, `Tag`.
* Technical items (e.g. `API`, `Class`, `Function`, `Repository`).

### 2. Relationship Edges
Edges are directional links connecting nodes:
* `Created By`, `Assigned To`, `Contains`, `Mentions`, `Depends On`, `References`, `Summarizes`, `Implements`, `Related To`, `Duplicates`, `Blocks`.

### 3. Evidence-Backed Edges
* Relationships must be explainable. Every edge stores an explicit reference/evidence tag (e.g. the specific `message_id` or `file_id` that established the relationship) to build client trust.

---

## Entity Extraction & Resolution Pipeline
Content processing feeds entities and relationships to the graph:

```text
Content Source -> Language Check -> Named Entity Recognition (NER) -> Entity Resolution -> Dedup -> Graph Node
```

* **Entity Resolution**: Normalizes variants of entity names to a single node record (e.g. merging "OpenAI", "Open AI", and "OpenAI Inc" to prevent graph duplicate noise).
* **Confidence Scores**: Extracted nodes and edges carry confidence values (`0.0` to `1.0`). Low-confidence items are withheld from graph queries until validated.

---

## MVP Storage & Graph Access API
* **Database Mapping**: For the MVP, graph relationships reside inside PostgreSQL join mapping tables. The data model abstracts graph lookups, facilitating future transitions to dedicated graph stores (Neo4j, Memgraph).
* **Permission Constraints**: Graph path searches and neighbor discovery queries inherit workspace ACL permissions. Hidden nodes are excluded from traversals to prevent security leaks.
* **APIs**: Exposes read-optimized queries for path searches, neighbor discovery, and knowledge map lookups.
