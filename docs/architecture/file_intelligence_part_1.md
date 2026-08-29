# File Intelligence & Storage Architecture (Part 1 — Object Storage, File Processing, Preview Engine, OCR & Metadata Extraction)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the complete File Intelligence Architecture of MindMesh. MindMesh treats every uploaded file as a searchable organizational knowledge asset, detailing storage adapters, upload pipelines, preview generators, OCR engines, metadata extractions, and version histories.

Every file-related module must comply with this document.

---

## Storage Abstraction & Bucket Layout
* **Storage Adapter**: Application modules interact only with a generalized adapter interface (abstracting operations like upload, download, exists, copy, delete), allowing swap-outs of S3-compatible providers (MinIO for development, AWS S3/Azure Blob for production).
* **Bucket Layout**: Object files reside in purpose-specific buckets (`avatars/`, `documents/`, `workspace-files/`, `conversation-files/`, `thumbnails/`, `previews/`).

---

## Upload Validation & Large File Strategy

### 1. Upload Validation
* Verification filters check file extension, MIME type, file size limits, duplicate SHA-256 hashes, and active workspace quotas before initiating storage writes.

### 2. Large File Handling
* **Multipart Uploads**: Files exceeding baseline sizes are split and uploaded as parallel chunks to support connection resume features and avoid loading entire files into server memory.
* **Streaming**: Binary retrieval uses streaming download streams instead of buffering bytes in memory.

### 3. Deduplication Check
* Incoming files are validated using **SHA-256 Checksums**. If the checksum matches an existing object, the database references the existing storage path, optimizing disk utilization.

---

## Asynchronous Preview & OCR Engines

### 1. Preview Generation
* Background workers generate previews (cached thumbnails, waveform images for audio, video snapshots, PDF first-page images) to render immediately on client cards.

### 2. OCR Processing
* Files flagged as screenshots, images, or scanned PDFs are routed through an **OCR pipeline** to extract text for semantic embedding chunking and keyword indices.

### 3. Metadata Extraction
* Extraction rules parse technical attributes (author, camera model, dimension size, durations, pages counts) and save them inside Pydantic JSONB attributes in `file_metadata`.

---

## Security & Version Control
* **Signed URLs**: All private files generate **temporary signed URLs** with a **10-minute expiration** window. Permanent public static object paths are disabled.
* **Versioning**: Replacing a file creates a new version entry in `file_versions`, keeping previous versions recoverable.
* **Deletes**: Files use soft-deletion by default, moving to retention holding before being permanently cleared from object storage.
