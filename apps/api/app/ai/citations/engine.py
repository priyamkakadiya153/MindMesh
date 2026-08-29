import re
import logging
from typing import List, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Citation
from .resolver import CitationResolver
from .validator import CitationValidator
from ..context.tokenizer import TokenBudgetManager

logger = logging.getLogger(__name__)

class CitationEngine:
    @staticmethod
    def calculate_text_similarity(str1: str, str2: str) -> float:
        """Computes simple token-level Jaccard similarity between two strings."""
        words1 = set(re.findall(r'\w+', str1.lower()))
        words2 = set(re.findall(r'\w+', str2.lower()))
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    @classmethod
    async def generate_citations(
        cls,
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        ai_response: str,
        retrieved_chunks: List[Dict[str, Any]],
        confidence_threshold: float = 0.35
    ) -> List[Citation]:
        """Resolves source chunks mentioned or implied in the AI response.
        
        Performs:
        - Manual footnote parsing (e.g. [1], [2] in text matches indices).
        - Sentence-level similarity overlap back-matching against retrieved chunks.
        - Security validation for all cited documents.
        """
        if not ai_response or not retrieved_chunks:
            return []
            
        citations_map: Dict[int, Citation] = {}
        
        # 1. Parse explicit footnote citations like [1], [2] in the AI response
        explicit_matches = re.findall(r'\[(\d+)\]', ai_response)
        explicit_indices = set(int(m) for m in explicit_matches)
        
        # 2. Perform sentence-level similarity auto-matching
        # Split into sentences (handling punctuation bounds)
        sentences = re.split(r'(?<=[.!?])\s+', ai_response)
        
        for sentence in sentences:
            if len(sentence.strip()) < 10:
                continue
                
            best_chunk = None
            best_similarity = 0.0
            best_chunk_idx = 0
            
            for idx, chunk in enumerate(retrieved_chunks, 1):
                sim = cls.calculate_text_similarity(sentence, chunk["content"])
                if sim > best_similarity:
                    best_similarity = sim
                    best_chunk = chunk
                    best_chunk_idx = idx
                    
            if best_chunk and best_similarity >= confidence_threshold:
                # We found a matching source chunk!
                doc_id = best_chunk.get("document_id")
                if doc_id:
                    try:
                        doc_uuid = UUID(str(doc_id))
                        # Resolve details
                        meta = await CitationResolver.resolve_source_metadata(db, doc_uuid)
                        if meta:
                            citation = Citation(
                                document=meta["document"],
                                document_id=meta["document_id"],
                                version=meta["version"],
                                workspace=meta["workspace"],
                                project=meta["project"],
                                page=best_chunk.get("page"),
                                section=best_chunk.get("metadata", {}).get("heading") or best_chunk.get("section"),
                                confidence=round(best_similarity, 4)
                            )
                            citations_map[best_chunk_idx] = citation
                    except Exception as e:
                        logger.error(f"Failed to generate citation for chunk {idx}: {str(e)}")

        # 3. Incorporate explicit references that might not have triggered high sentence similarity
        for idx in explicit_indices:
            if idx in citations_map:
                continue # Already resolved
                
            if 0 < idx <= len(retrieved_chunks):
                chunk = retrieved_chunks[idx - 1]
                doc_id = chunk.get("document_id")
                if doc_id:
                    try:
                        doc_uuid = UUID(str(doc_id))
                        meta = await CitationResolver.resolve_source_metadata(db, doc_uuid)
                        if meta:
                            citations_map[idx] = Citation(
                                document=meta["document"],
                                document_id=meta["document_id"],
                                version=meta["version"],
                                workspace=meta["workspace"],
                                project=meta["project"],
                                page=chunk.get("page"),
                                section=chunk.get("metadata", {}).get("heading") or chunk.get("section"),
                                confidence=0.80 # Assume high since explicitly cited
                            )
                    except Exception:
                        pass

        # 4. Security validation: Verify user has access to all cited document IDs
        citations_list = list(citations_map.values())
        if not citations_list:
            return []
            
        cited_doc_ids = [c.document_id for c in citations_list]
        is_authorized = await CitationValidator.validate_citation_permissions(
            db=db,
            user_id=user_id,
            org_id=org_id,
            document_ids=cited_doc_ids
        )
        
        if not is_authorized:
            # Filter individually
            filtered_citations = []
            for citation in citations_list:
                auth = await CitationValidator.validate_citation_permissions(
                    db=db,
                    user_id=user_id,
                    org_id=org_id,
                    document_ids=[citation.document_id]
                )
                if auth:
                    filtered_citations.append(citation)
            return filtered_citations
            
        return citations_list
