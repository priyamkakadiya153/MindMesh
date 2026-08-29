# AI Architecture (Part 1 — AI System Design, RAG Pipeline & Knowledge Intelligence Engine)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official Artificial Intelligence architecture of MindMesh. MindMesh uses AI to transform organizational conversations and files into a continuously growing knowledge system.

---

## AI System & RAG Philosophy
MindMesh is **AI-Augmented**, not AI-Centric.
* **Retrieval First**: All queries must execute hybrid vector and database retrieval *before* calling LLMs to prevent hallucinated answers.
* **Explainability**: Every generated answer must return source citations linking directly to the primary database message or file.
* **Security Isolation**: Resource visibility (Workspace, Project membership) must be checked and filtered *before* retrieved context results are sent to ranking or generation stages.

---

## Hybrid Retrieval Pipeline Flow
MindMesh utilizes a dual-path retrieval pipeline:

```text
User Question -> Permission Verification -> Query Embedding
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        ▼                                             ▼
                 Semantic Search                               Keyword Search
                   (ChromaDB)                                   (PostgreSQL)
                        │                                             │
                        └──────────────────────┬──────────────────────┘
                                               ▼
                                     Merged Context List
                                               │
                                               ▼
                                      RBAC Filter Check
                                               │
                                               ▼
                                       Context Ranking
                                               │
                                               ▼
                                         Prompt Builder
                                               │
                                               ▼
                                            LLM Call
                                               │
                                               ▼
                                    Response + Source Link
```

1. **Semantic Search**: Powered by ChromaDB and Sentence Transformers. Captures similarity, semantic intent, and related topics.
2. **Keyword Search**: Powered by PostgreSQL indexing. Captures exact terms, filenames, and IDs.
3. **Context Ranking**: Merges results, applies recency factors, and keeps only the highest relevance chunks fitting within token parameters.

---

## AI Provider Abstraction Layer
* Business features interact only with a generalized AI interface (e.g. `EmbeddingService`, `TextGenerationService`).
* The engine remains provider-independent, supporting interchangeable models:
  * Gemini (Default)
  * OpenAI
  * Anthropic
  * Mistral
  * DeepSeek / Local Llama setups
* Configurable token routing routes simple requests to light models, and complex semantic synthesis to large reasoning models.
