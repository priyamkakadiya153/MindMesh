# Search & Knowledge Discovery Architecture (Part 2 — Ranking Engine, Personalization, Knowledge Graph Search, Recommendation Engine & Advanced Retrieval)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines how MindMesh transforms search results into intelligent knowledge discovery. It covers multi-stage ranking pipelines, Reciprocal Rank Fusion (RRF), cross-encoder re-ranking algorithms, context-aware personalized factors, graph traversals, and discovery recommendation engines.

---

## Multi-Stage Ranking Pipeline
MindMesh matches queries to candidates using a layered re-ranking pipeline:

```text
Candidates (Keyword/Vector/Graph) -> Initial RRF Score -> Context Adjustments -> Cross-Encoder Re-ranker -> Final ACL Pass -> Results
```

1. **Candidate Retrieval**: Merges keyword index lists, vector outputs, and graph nodes.
2. **Initial Scoring (RRF)**: Combines keyword, semantic similarity, and graph relevance rankings into a single sorted list.
3. **Context Weighting**: Adjusts scores using current project scopes, user roles, active workspaces, and recent documents history.
4. **Cross-Encoder Re-ranking**: Routes the top candidate set through an AI re-ranker model to verify contextual alignment.
5. **Final ACL Filter**: Verifies that the client holds read access permission for every resource in the list.

---

## Reciprocal Rank Fusion (RRF) & Re-ranking
* **RRF Score Fusion**: Combines search rankings from disparate engines (PostgreSQL FTS, ChromaDB Vector Similarity, Neo4j/Relational Graph traversal) without requiring raw score normalizations.
* **Cross-Encoder Limit**: Re-ranking runs asynchronously and is restricted strictly to the top candidate set (e.g. top 10–20 results) to prevent API latency spikes.

---

## Knowledge Graph & Relationship Search
Search queries traverse relations to fetch interconnected knowledge nodes:
* **Graph Relations**: Matches track directional links (`Referenced By`, `Mentions`, `Depends On`, `Created From`, `Summarized By`).
* **Multi-hop Retrieval**: Follows graph connections to answer cross-entity questions (e.g. tracking a task back to its meeting conversation and original project specifications doc).

---

## Recommendation Engine & Analytics Feedback
* **Recommendations**: Computes cosine similarities across text embeddings to suggest relevant resources, files, and discussion logs without direct user search terms.
* **Feedback Loop**: Tracks user click-throughs and relevance markings (`Helpful` / `Not Helpful`) to adjust re-ranking coefficients over time.

---

## Target Performance Benchmarks (P95)
* **Query Understanding**: < 50 ms
* **Hybrid Retrieval**: < 500 ms
* **RRF Scoring**: < 20 ms
* **Re-ranking**: < 150 ms
* **Knowledge Graph Search**: < 200 ms
* **Total P95 Search Latency**: < 700 ms
