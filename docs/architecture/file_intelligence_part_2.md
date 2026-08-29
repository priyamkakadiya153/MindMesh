# File Intelligence & Storage Architecture (Part 2 — Document Intelligence, Chunking Strategy, File Collaboration, Version Control & Advanced File Search)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines how MindMesh transforms uploaded files into intelligent, collaborative, AI-powered knowledge assets. It covers multi-format content parsers, text normalizations, semantic heading chunking, cross-document entity linking, annotation layers, and advanced file search filters.

Every file-related module must comply with this document.

---

## Document Intelligence Pipeline
Each document format routes to a dedicated parser (PDF, DOCX, presentation, images, or code) before text extraction:
1. **Text Normalization**: Parsed outputs are cleaned of duplicate whitespace and normalized to Unicode formats while preserving headings, lists, tables, and code blocks.
2. **Language Detection**: Automatically tags languages (English, Hindi, Gujarati, French, German) to guide model prompting.
3. **AI Classification**: Documents are classified (Contracts, Meeting Notes, Source Code, Invoices) to filter retrieval pools.

---

## Adaptive Chunking & Incremental Indexing
* **Adaptive Sizing**: Chunk token limits adjust by category (definitions use small chunks; articles medium; research papers large).
* **Chunk Metadata**: Chunks track `page_number`, `heading`, `language`, and parent `file_id`.
* **Incremental Reindexing**: Upon file updates, the diff engine identifies modified text sections, regenerating vectors only for changed blocks to minimize provider costs.

---

## Knowledge Linking & Entity Extraction
* **Graph Linking**: Discovery pipelines automatically extract entities (people, technologies, workspace dates, location names, classes) and link them to build an organizational knowledge graph.
* **Citation Engines**: Generation outputs reference the exact page, header, and chunk context.

---

## Collaboration & Annotation Layers
Users can create highlights, bookmarks, and comments.
* **Annotation Isolation**: Comments, highlights, and annotations are saved as relational logs inside PostgreSQL and *never* modify the primary file binary.
* **Comment Scopes**: Comment logs link to exact selections (`page_number`, `paragraph_index`, or coordinates).
