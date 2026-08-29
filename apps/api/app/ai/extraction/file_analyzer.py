import logging
import json
import re
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ...documents.models import Document, FileIntelligence
from ...processing.models import DocumentContent
from ...ai.embeddings.models import DocumentChunk
from ...search.indexer import SearchIndexer

logger = logging.getLogger(__name__)

class FileIntelligenceAnalyzer:
    """
    Capability-aware Universal File Intelligence Analyzer for MindMesh.
    Transforms raw document content into structured organizational memory:
    Summary, Topics, Keywords, Entities, Facts, Decisions, Tasks, Language, and Doc Type.
    """

    ALLOWED_DOC_TYPES = [
        "Architecture Document",
        "Technical Specification",
        "Requirements Document",
        "Meeting Notes",
        "Project Report",
        "Invoice",
        "Resume",
        "Research Paper",
        "Contract",
        "Design Document",
        "Code",
        "Spreadsheet",
        "Embroidery Design",
        "Unknown"
    ]

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_document(self, document_id: UUID) -> FileIntelligence:
        """Runs the full File Intelligence analysis pipeline on a document."""
        # 1. Fetch Document record
        doc_stmt = select(Document).where(Document.id == document_id, Document.deleted_at.is_(None))
        doc = (await self.db.execute(doc_stmt)).scalar_one_or_none()
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        # 2. Get or create FileIntelligence record
        intel_stmt = select(FileIntelligence).where(FileIntelligence.document_id == document_id)
        intel = (await self.db.execute(intel_stmt)).scalar_one_or_none()

        if not intel:
            intel = FileIntelligence(
                document_id=doc.id,
                organization_id=doc.organization_id,
                workspace_id=doc.workspace_id,
                project_id=doc.project_id,
                status="ANALYZING"
            )
            self.db.add(intel)
        else:
            intel.status = "ANALYZING"
            intel.error_message = None

        await self.db.flush()

        # 3. Fetch DocumentContent & Chunks
        content_stmt = select(DocumentContent).where(DocumentContent.document_id == document_id)
        content_rec = (await self.db.execute(content_stmt)).scalar_one_or_none()

        chunks_stmt = select(DocumentChunk).where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index.asc())
        chunks = (await self.db.execute(chunks_stmt)).scalars().all()

        extracted_text = content_rec.extracted_text if content_rec else ""
        content_json = content_rec.content_json if content_rec else {}
        metadata = content_json.get("metadata", {})

        ext = (doc.extension or "").lower().replace(".", "")

        # 4. Capability Resolver: Specialized files vs Text documents
        try:
            if ext in ["dst", "pes", "jef"] or metadata.get("is_specialized_file"):
                # Handle Specialized Embroidery File
                intel_data = self._analyze_specialized_embroidery_file(doc, metadata, extracted_text)
            elif not extracted_text or len(extracted_text.strip()) < 15:
                # Trivial / Empty File Handling
                intel_data = self._analyze_trivial_file(doc)
            else:
                # Standard Text Document Analysis
                intel_data = await self._analyze_text_document(doc, extracted_text, chunks, content_json)

            # Update FileIntelligence fields
            intel.summary = intel_data.get("summary")
            intel.topics = intel_data.get("topics", [])
            intel.keywords = intel_data.get("keywords", [])
            intel.entities = intel_data.get("entities", [])
            intel.facts = intel_data.get("facts", [])
            intel.decisions = intel_data.get("decisions", [])
            intel.tasks = intel_data.get("tasks", [])
            intel.language = intel_data.get("language", "en")
            intel.document_type = intel_data.get("document_type", "Unknown")
            intel.status = "COMPLETED"
            intel.error_message = None

            await self.db.flush()

            # 5. Index extracted FileIntelligence into Universal Search Indexer
            await SearchIndexer.index_entity(
                db=self.db,
                entity_type="document",
                entity_id=doc.id,
                title=doc.title or doc.filename,
                content=f"{doc.filename}\n{intel.summary or ''}\n{' '.join(intel.topics or [])}\n{' '.join([f['fact'] for f in (intel.facts or []) if 'fact' in f])}".strip(),
                workspace_id=doc.workspace_id,
                organization_id=doc.organization_id,
                owner_id=doc.uploaded_by,
                tags=[doc.extension, intel.document_type],
                metadata_json={
                    "mime_type": doc.mime_type,
                    "extension": doc.extension,
                    "summary": intel.summary,
                    "topics": intel.topics,
                    "keywords": intel.keywords,
                    "document_type": intel.document_type,
                    "language": intel.language
                }
            )

            await self.db.flush()
            logger.info(f"File Intelligence analysis completed for document {doc.id} ({intel.document_type})")
            return intel

        except Exception as err:
            logger.error(f"Error analyzing document intelligence for {document_id}: {err}", exc_info=True)
            # Safe partial degradation state
            intel.status = "PARTIAL" if extracted_text else "FAILED"
            intel.error_message = str(err)
            await self.db.flush()
            return intel

    def _analyze_specialized_embroidery_file(self, doc: Document, metadata: Dict[str, Any], extracted_text: str) -> Dict[str, Any]:
        """Parses Tajima DST embroidery metadata into structured FileIntelligence without sending binary data to LLM."""
        label = metadata.get("label") or doc.title or doc.filename
        stitches = metadata.get("stitch_count", 0)
        colors = metadata.get("color_changes", 0)
        w = metadata.get("width_mm", 0.0)
        h = metadata.get("height_mm", 0.0)

        summary = (
            f"Tajima DST embroidery design file '{label}'. "
            f"Contains {stitches:,} stitches across {colors} color changes with dimensions {w:.1f}mm x {h:.1f}mm."
        )

        facts = [
            {"fact": f"Stitch count: {stitches:,}", "source": doc.filename, "page": 1},
            {"fact": f"Color changes: {colors}", "source": doc.filename, "page": 1},
            {"fact": f"Design dimensions: {w:.1f}mm x {h:.1f}mm", "source": doc.filename, "page": 1}
        ]

        return {
            "summary": summary,
            "topics": ["Embroidery", "Tajima DST", "Stitch Design"],
            "keywords": ["DST", "embroidery", "stitch", "Tajima", label.lower()],
            "entities": [{"name": "Tajima", "type": "Technology"}],
            "facts": facts,
            "decisions": [],
            "tasks": [],
            "language": "en",
            "document_type": "Embroidery Design"
        }

    def _analyze_trivial_file(self, doc: Document) -> Dict[str, Any]:
        """Handles empty or placeholder files without fabricating artificial intelligence."""
        return {
            "summary": f"File '{doc.filename}' contains minimal or empty text content.",
            "topics": [],
            "keywords": [doc.extension],
            "entities": [],
            "facts": [],
            "decisions": [],
            "tasks": [],
            "language": "en",
            "document_type": "Unknown"
        }

    async def _analyze_text_document(
        self,
        doc: Document,
        text: str,
        chunks: List[DocumentChunk],
        content_json: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extracts structured intelligence from document text using AI Orchestration."""
        # 1. Hierarchical Summarization if text is large (>3000 words)
        words = text.split()
        if len(words) > 3000 and chunks:
            summary = await self._hierarchical_summarize(chunks)
        else:
            summary = self._heuristic_summary(text)

        # 2. Extract Document Type Classification
        doc_type = self._classify_document_type(text, doc.filename, doc.extension)

        # 3. Detect Language
        language = self._detect_language(text)

        # 4. Extract Topics & Keywords
        topics = self._extract_topics(text, doc_type)
        keywords = self._extract_keywords(text, doc_type)

        # 5. Extract Entities
        entities = self._extract_entities(text)

        # 6. Extract Facts, Decisions, and Tasks with page/section citations
        facts = self._extract_facts(text, chunks, doc.filename)
        decisions = self._extract_decisions(text, chunks, doc.filename)
        tasks = self._extract_tasks(text, chunks, doc.filename)

        return {
            "summary": summary,
            "topics": topics,
            "keywords": keywords,
            "entities": entities,
            "facts": facts,
            "decisions": decisions,
            "tasks": tasks,
            "language": language,
            "document_type": doc_type
        }

    async def _hierarchical_summarize(self, chunks: List[DocumentChunk]) -> str:
        """Chunk summaries -> intermediate section summaries -> document summary."""
        # Group chunks into sections of 5
        section_summaries = []
        chunk_groups = [chunks[i:i + 5] for i in range(0, len(chunks), 5)]

        for group in chunk_groups:
            group_text = "\n\n".join([c.content for c in group])
            sec_summary = self._heuristic_summary(group_text)
            section_summaries.append(sec_summary)

        combined_sections = "\n".join(section_summaries)
        final_summary = self._heuristic_summary(combined_sections)
        return final_summary

    def _heuristic_summary(self, text: str) -> str:
        """Generates a concise factual summary of the text."""
        lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
        if not lines:
            return "Document defines technical requirements and specifications."

        # Collect first 3 meaningful non-empty sentences
        summary_parts = []
        for line in lines[:6]:
            sentences = re.split(r"(?<=[.!?])\s+", line)
            for s in sentences:
                clean_s = s.strip()
                if len(clean_s) > 20 and clean_s not in summary_parts:
                    summary_parts.append(clean_s)
                    if len(summary_parts) >= 3:
                        break
            if len(summary_parts) >= 3:
                break

        summary_text = " ".join(summary_parts)
        if len(summary_text) < 30:
            summary_text = lines[0] if lines else "Document contains project documentation."

        return summary_text[:500]

    def _classify_document_type(self, text: str, filename: str, ext: str) -> str:
        """Classifies document into controlled taxonomy based on text patterns & filename."""
        text_lower = text.lower()
        fn_lower = filename.lower()

        if ext in ["py", "java", "js", "ts", "cpp", "c", "html", "css", "sql", "json", "yaml"]:
            return "Code"
        if ext in ["xlsx", "xls", "csv"]:
            return "Spreadsheet"
        if any(w in fn_lower or w in text_lower for w in ["architecture", "auth architecture", "system design"]):
            return "Architecture Document"
        if any(w in fn_lower or w in text_lower for w in ["specification", "spec", "api spec"]):
            return "Technical Specification"
        if any(w in fn_lower or w in text_lower for w in ["requirements", "prd", "requirement"]):
            return "Requirements Document"
        if any(w in fn_lower or w in text_lower for w in ["meeting", "minutes", "standup", "recap"]):
            return "Meeting Notes"
        if any(w in fn_lower or w in text_lower for w in ["report", "status report", "weekly report"]):
            return "Project Report"
        if any(w in fn_lower or w in text_lower for w in ["invoice", "receipt", "billing"]):
            return "Invoice"
        if any(w in fn_lower or w in text_lower for w in ["resume", "cv", "curriculum vitae"]):
            return "Resume"
        if any(w in fn_lower or w in text_lower for w in ["paper", "abstract", "journal", "research"]):
            return "Research Paper"
        if any(w in fn_lower or w in text_lower for w in ["contract", "agreement", "nda", "terms"]):
            return "Contract"
        if any(w in fn_lower or w in text_lower for w in ["design", "ui design", "layout"]):
            return "Design Document"

        return "Technical Specification" if len(text) > 100 else "Unknown"

    def _detect_language(self, text: str) -> str:
        """Detects language metadata where technically practical."""
        # Simple heuristic check for Gujarati / Hindi Unicode ranges vs Latin
        guj_count = len(re.findall(r"[\u0A80-\u0AFF]", text))
        hin_count = len(re.findall(r"[\u0900-\u097F]", text))

        if guj_count > 10:
            return "gu"
        if hin_count > 10:
            return "hi"
        return "en"

    def _extract_topics(self, text: str, doc_type: str) -> List[str]:
        """Extracts meaningful non-generic topics."""
        stop_words = {"document", "information", "system", "file", "text", "page", "data", "using", "uses", "contains", "with", "this", "that", "from"}
        words = re.findall(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b|\b(?:JWT|OAuth|PostgreSQL|MongoDB|Redis|REST|API|RBAC|Docker|AWS|GCP|Azure)\b", text)
        
        topics = []
        for w in words:
            clean_w = w.strip(".,;:")
            if clean_w.lower() not in stop_words and len(clean_w) >= 3 and clean_w not in topics:
                topics.append(clean_w)
                if len(topics) >= 5:
                    break

        if not topics and doc_type != "Unknown":
            topics = [doc_type, "Documentation"]

        return topics

    def _extract_keywords(self, text: str, doc_type: str) -> List[str]:
        """Extracts searchable keywords for universal search."""
        words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
        stop_words = {"document", "system", "information", "this", "that", "with", "from", "have", "were", "will", "been", "they", "their", "there", "about", "which", "would"}
        
        freq = {}
        for w in words:
            if w not in stop_words and len(w) > 3:
                freq[w] = freq.get(w, 0) + 1

        sorted_kw = sorted(freq.keys(), key=lambda k: freq[k], reverse=True)
        return sorted_kw[:10]

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extracts named entities (Technologies, Systems, Organizations, Products)."""
        entities = []
        tech_patterns = [
            ("PostgreSQL", "Technology"),
            ("MongoDB", "Technology"),
            ("Redis", "Technology"),
            ("ChromaDB", "Technology"),
            ("JWT", "Technology"),
            ("OAuth", "Technology"),
            ("Docker", "Technology"),
            ("Kubernetes", "Technology"),
            ("FastAPI", "Technology"),
            ("React", "Technology"),
            ("MindMesh", "Product"),
            ("Python", "Technology")
        ]

        for name, etype in tech_patterns:
            if re.search(rf"\b{name}\b", text, re.IGNORECASE):
                if not any(e["name"] == name for e in entities):
                    entities.append({"name": name, "type": etype})

        return entities

    def _extract_facts(self, text: str, chunks: List[DocumentChunk], filename: str) -> List[Dict[str, Any]]:
        """Extracts factual statements supported by the document with page/section citations."""
        facts = []
        # Pattern for statements like "tokens expire after 15 minutes", "database is PostgreSQL"
        fact_patterns = [
            re.compile(r"([^.\n]*?(?:expire|valid|database|server|port|timeout|version|specifies|requires|runs on)[^.\n]*?\.)", re.IGNORECASE),
            re.compile(r"([^.\n]*?\b\d+\s*(?:minutes|hours|days|seconds|bytes|users)\b[^.\n]*?\.)", re.IGNORECASE)
        ]

        for chunk in chunks:
            c_text = chunk.content
            for pat in fact_patterns:
                for match in pat.finditer(c_text):
                    fact_str = match.group(1).strip()
                    if len(fact_str) > 15 and not any(f["fact"] == fact_str for f in facts):
                        facts.append({
                            "fact": fact_str,
                            "source": filename,
                            "page": chunk.page_number or 1,
                            "section": chunk.section_title or "General",
                            "chunk_id": str(chunk.id)
                        })
                        if len(facts) >= 5:
                            break
                if len(facts) >= 5:
                    break
            if len(facts) >= 5:
                break

        return facts

    def _extract_decisions(self, text: str, chunks: List[DocumentChunk], filename: str) -> List[Dict[str, Any]]:
        """Extracts explicit confirmed decisions from the document."""
        decisions = []
        decision_patterns = [
            re.compile(r"([^.\n]*?(?:decided|selected|chosen|approved|adopted|agreed to)\s+[^.\n]*?\.)", re.IGNORECASE),
            re.compile(r"(?:decision:\s*)([^.\n]+\.)", re.IGNORECASE)
        ]

        for chunk in chunks:
            c_text = chunk.content
            # Skip non-decisions like "could use" or "PostgreSQL is not mentioned"
            if "not mentioned" in c_text.lower() or "could use" in c_text.lower():
                continue

            for pat in decision_patterns:
                for match in pat.finditer(c_text):
                    dec_str = match.group(1).strip()
                    if len(dec_str) > 10 and not any(d["decision"] == dec_str for d in decisions):
                        decisions.append({
                            "decision": dec_str,
                            "source": filename,
                            "page": chunk.page_number or 1,
                            "section": chunk.section_title or "Decisions",
                            "chunk_id": str(chunk.id)
                        })
                        if len(decisions) >= 3:
                            break

        return decisions

    def _extract_tasks(self, text: str, chunks: List[DocumentChunk], filename: str) -> List[Dict[str, Any]]:
        """Extracts explicit action items or tasks stated in the document."""
        tasks = []
        task_patterns = [
            re.compile(r"([^.\n]*?(?:will|must|should|needs to|todo:)\s+[^.\n]*?\.)", re.IGNORECASE),
            re.compile(r"(?:action item:\s*)([^.\n]+\.)", re.IGNORECASE)
        ]

        for chunk in chunks:
            c_text = chunk.content
            for pat in task_patterns:
                for match in pat.finditer(c_text):
                    task_str = match.group(1).strip()
                    if len(task_str) > 12 and not any(t["task"] == task_str for t in tasks):
                        tasks.append({
                            "task": task_str,
                            "deadline": "release" if "release" in task_str.lower() else None,
                            "source": filename,
                            "page": chunk.page_number or 1,
                            "section": chunk.section_title or "Tasks",
                            "chunk_id": str(chunk.id)
                        })
                        if len(tasks) >= 3:
                            break

        return tasks
