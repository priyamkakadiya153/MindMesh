# Search & Knowledge Discovery Architecture (Part 1 — Universal Search, Hybrid Retrieval, Query Processing & Search Engine Design)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the Search & Knowledge Discovery Architecture for MindMesh. It specifies the query processing pipeline, intent detection filters, hybrid search routing (integrating vector database recall and relational database keyword matches), permission verification filters, and search autocomplete indicators.

Every search query, index updates, and results display must comply with this document.

---

## Query Processing & Understanding
Before matching database index tables, user inputs pass through a strict query processing pipeline:
1. **Query Normalization**: Standardizes Unicode characters, removes duplicate whitespace, and strips punctuation.
2. **Intent Detection**: Analyzes if the user seeks files, conversations, tasks, decisions, or people, to adjust rankings.
3. **Entity Recognition**: Identifies entities (technologies, users, project names, timeline dates) to filter index ranges.
4. **Query Expansion**: Automatically expands common abbreviations and aliases (e.g. `RAG` expands to `Retrieval-Augmented Generation`).

---

## Hybrid Retrieval Strategy
Universal Search balances Keyword Precision and Semantic Recall by routing searches in parallel:

```text
User Query -> Query Embedding -> Vector search (ChromaDB)
           └───────────────────> Full-text search (PostgreSQL) 
                                           │
                                           ▼
                                 Score Fusion & Ranking
                                           │
                                           ▼
                                 ACL Permission Filter
                                           │
                                           ▼
                                    Rendered Results
```

* **Keyword Search**: Uses PostgreSQL full-text index parameters for exact token and prefix matches.
* **Semantic Search**: Uses ChromaDB cosine similarity checks to surface contextually related knowledge.
* **Score Fusion**: Merges indices into a single relevancy score, prioritizing fresh, high-relevancy, and contextually matching objects.

---

## Security & Permission Filtering
* **Pre-Filtering Verification**: Security checks validate that the user is authorized to view the resource *before* matching results or scoring vectors.
* **Scope Verification**: Results verify workspace memberships, project enrollments, and private room invite keys. Stale or unauthorized vectors are excluded before score sorting.

---

## Autocomplete & Performance Latencies
* **Autocomplete Suggestions**: Feeds from active users, project channels, and tags, rendering suggestions under **100 ms**.
* **Target Latency Limits**:
  * Autocomplete: < 100 ms
  * Keyword Search: < 200 ms
  * Semantic Search: < 500 ms
  * Hybrid Search: < 700 ms
