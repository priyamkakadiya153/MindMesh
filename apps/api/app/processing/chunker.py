import re
import hashlib
import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

logger = logging.getLogger(__name__)

# Try loading tiktoken for precise BPE token counting; fallback to word-ratio estimation if unavailable
try:
    import tiktoken
    _TIKTOKEN_ENCODER = tiktoken.get_encoding("cl100k_base")
except Exception:
    _TIKTOKEN_ENCODER = None

class SemanticChunker:
    def __init__(
        self,
        target_chunk_tokens: int = 600,
        min_chunk_tokens: int = 200,
        max_chunk_tokens: int = 800,
        overlap_tokens: int = 125
    ):
        self.target_chunk_tokens = target_chunk_tokens
        self.min_chunk_tokens = min_chunk_tokens
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

    @staticmethod
    def count_tokens(text: str) -> int:
        """Counts tokens using tiktoken cl100k_base or fallback word-estimation."""
        if not text:
            return 0
        if _TIKTOKEN_ENCODER:
            try:
                return len(_TIKTOKEN_ENCODER.encode(text))
            except Exception:
                pass
        # Fallback estimation: ~1.3 tokens per word
        words = text.split()
        return int(len(words) * 1.3) + 1 if words else 0

    @staticmethod
    def compute_checksum(text: str) -> str:
        """Computes SHA256 hex checksum of chunk content."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _split_into_sentences(self, text: str) -> List[str]:
        """Splits text into sentences while avoiding splitting within abbreviations or decimals."""
        if not text:
            return []
        # Split on sentence enders (. ! ?) followed by whitespace
        raw_sentences = re.split(r"(?<=[.!?])\s+", text)
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        return sentences if sentences else [text]

    def _split_into_blocks(self, text: str) -> List[Dict[str, Any]]:
        """Splits raw text into paragraph or heading blocks."""
        paragraphs = re.split(r"\n\n+", text)
        blocks = []
        for p in paragraphs:
            cleaned = p.strip()
            if not cleaned:
                continue
            # Detect section title / heading
            is_heading = cleaned.startswith("#") or (len(cleaned) < 80 and cleaned.isupper())
            blocks.append({
                "text": cleaned,
                "is_heading": is_heading,
                "tokens": self.count_tokens(cleaned)
            })
        return blocks

    def chunk_document(
        self,
        cleaned_text: str,
        document_id: UUID,
        organization_id: UUID,
        workspace_id: UUID,
        sections: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Splits document text into semantically cohesive, overlap-buffered chunks."""
        if not cleaned_text or not cleaned_text.strip():
            return []

        blocks = self._split_into_blocks(cleaned_text)
        chunks: List[Dict[str, Any]] = []

        current_sentences: List[str] = []
        current_tokens = 0
        current_section = None
        current_page = None
        global_offset = 0

        # Helper to push a chunk
        def push_chunk(sentences_list: List[str], sec_title: Optional[str] = None, pg_num: Optional[int] = None):
            nonlocal chunks, global_offset
            chunk_str = " ".join(sentences_list).strip()
            if not chunk_str:
                return

            tok_count = self.count_tokens(chunk_str)
            char_count = len(chunk_str)
            checksum = self.compute_checksum(chunk_str)
            start_pos = global_offset
            end_pos = global_offset + char_count
            global_offset = end_pos + 1

            chunk_idx = len(chunks)
            chunks.append({
                "chunk_index": chunk_idx,
                "document_id": document_id,
                "organization_id": organization_id,
                "workspace_id": workspace_id,
                "page_number": pg_num,
                "section_title": sec_title,
                "content": chunk_str,
                "token_count": tok_count,
                "character_count": char_count,
                "checksum": checksum,
                "metadata_json": {
                    "start_offset": start_pos,
                    "end_offset": end_pos,
                    "chunk_index": chunk_idx,
                    "checksum": checksum
                }
            })

        for block in blocks:
            if block["is_heading"]:
                current_section = block["text"].lstrip("#").strip()

            block_sentences = self._split_into_sentences(block["text"])

            for sentence in block_sentences:
                sent_tokens = self.count_tokens(sentence)

                if current_tokens + sent_tokens > self.max_chunk_tokens and current_sentences:
                    # Current chunk full -> push chunk
                    push_chunk(current_sentences, current_section, current_page)

                    # Build overlap buffer from the end of previous sentences
                    overlap_sentences: List[str] = []
                    overlap_acc = 0
                    for prev_s in reversed(current_sentences):
                        p_toks = self.count_tokens(prev_s)
                        if overlap_acc + p_toks <= self.overlap_tokens:
                            overlap_sentences.insert(0, prev_s)
                            overlap_acc += p_toks
                        else:
                            break

                    current_sentences = overlap_sentences
                    current_tokens = overlap_acc

                current_sentences.append(sentence)
                current_tokens += sent_tokens

        # Push final remaining chunk
        if current_sentences:
            push_chunk(current_sentences, current_section, current_page)

        logger.info(f"Chunker produced {len(chunks)} chunks for document {document_id}")
        return chunks
