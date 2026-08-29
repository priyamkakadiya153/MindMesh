# AI Architecture (Part 2 — Embedding Engine, Chunking Strategy, Hybrid Retrieval & Context Ranking)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the core intelligence engine of MindMesh. It specifies how information is converted into embeddings, divided into semantic chunks, retrieved from multiple knowledge sources, ranked, and delivered to the Large Language Model.

This document defines how MindMesh thinks before the LLM generates an answer.

---

## Embedding & Version Control
* **Target Embeddings**: Generated for messages, conversation windows, files, summaries, tasks, and decisions.
* **Metadata Scope**: Every vector links to `workspace_id`, `project_id`, `conversation_id`, `file_id`, `message_id`, and `created_at`.
* **Model Logging**: Model name, model version, and generation date are stored to enable vector regeneration when models are upgraded.

---

## Chunking Strategy

### 1. Document Chunking
* **Standard Size**: **512 Tokens**
* **Overlap**: **64–128 Tokens** (preserves semantic context across splits)
* **Heading-Based**: Splits on headers (`H1`, `H2`, `H3`) for markdown or HTML.
* **Paragraph-Based**: Splits on double line-breaks for simple notes.

### 2. Specialized Chunking
* **Code Chunking**: Split by functions, classes, and modules (never split code arbitrarily).
* **Spreadsheet Chunking**: Split by individual sheets, table headers, and regions.
* **Conversation Chunking**: Split by time windows, topic shifts, or message counts rather than fixed token limits.

---

## Hybrid Retrieval & Ranking

### 1. Hybrid Retrieval Flow
* **Semantic Path**: ChromDB vector similarity matching (captures meaning and similar concepts).
* **Keyword Path**: PostgreSQL indexed query matching (captures exact words, tags, and IDs).
* **Pre-Filtering**: Metadata and visibility permissions are filtered *before* ranking.

### 2. Context Ranking & Re-ranking
* Merged candidates are scored based on semantic similarity, keyword matches, recency, file importance, and user active context.
* Optional second-pass re-ranking is executed using Cross-Encoders or lightweight re-rankers to maximize retrieval accuracy.

---

## Caching & Performance Goals
To keep response times immediate, retrieval caches query hashes and vector results inside Redis.

### Performance Targets
* **Embedding Generation**: < 500 ms (small text)
* **Retrieval**: < 150 ms
* **Hybrid Search**: < 300 ms
* **Ranking**: < 100 ms
* **Total AI Context Build**: < 600 ms
