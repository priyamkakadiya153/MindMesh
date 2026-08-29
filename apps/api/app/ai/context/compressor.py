import re
import logging
from typing import List, Dict, Any
from .tokenizer import TokenBudgetManager

logger = logging.getLogger(__name__)

class ContextCompressor:
    @staticmethod
    def compress_chunks(
        chunks: List[Dict[str, Any]],
        token_limit: int,
        query: str = ""
    ) -> List[Dict[str, Any]]:
        """Compresses context chunks to fit within a specific token budget.
        
        Process:
        1. Remove exact duplicate contents.
        2. If total tokens exceed limit, filter out lower relevance chunks.
        3. If still exceeding, perform sentence-level extractive compression on larger chunks
           prioritizing query keywords.
        """
        if not chunks or token_limit <= 0:
            return []

        # Count current tokens
        for chunk in chunks:
            if "token_count" not in chunk or chunk["token_count"] <= 0:
                chunk["token_count"] = TokenBudgetManager.count_tokens(chunk["content"])
                
        total_tokens = sum(c["token_count"] for c in chunks)
        if total_tokens <= token_limit:
            return chunks
            
        logger.info(f"Context total tokens {total_tokens} exceeds limit {token_limit}. Compressing...")

        # Step 1: Keep chunks within limit by sorting by relevance and dropping low-ranking ones
        retained_chunks = []
        current_tokens = 0
        
        # Sort by ranking score or score first
        sorted_chunks = sorted(chunks, key=lambda x: x.get("ranking_score", x.get("score", 0.0)), reverse=True)
        
        for chunk in sorted_chunks:
            if current_tokens + chunk["token_count"] <= token_limit:
                retained_chunks.append(chunk)
                current_tokens += chunk["token_count"]
            else:
                # We reached a chunk that pushes us over. Keep it and compress it, or just stop.
                # Let's compress the remaining candidates to extract only query-relevant sentences.
                needed_budget = token_limit - current_tokens
                if needed_budget > 5: # Only compress if there's reasonable budget left
                    compressed_chunk = ContextCompressor.compress_single_chunk(chunk, needed_budget, query)
                    if compressed_chunk and compressed_chunk["token_count"] > 0:
                        retained_chunks.append(compressed_chunk)
                        current_tokens += compressed_chunk["token_count"]
                break
                
        return retained_chunks

    @staticmethod
    def compress_single_chunk(chunk: Dict[str, Any], target_tokens: int, query: str) -> Dict[str, Any]:
        """Compresses a single chunk to fit target_tokens by selecting key sentences."""
        content = chunk["content"]
        # Split into sentences using a regex (handles periods followed by spaces/newlines)
        sentences = re.split(r'(?<=[.!?])\s+', content)
        if len(sentences) <= 1:
            # Can't compress sentence-wise, truncate text by char approximation
            approx_chars = target_tokens * 4
            truncated = content[:approx_chars]
            new_chunk = chunk.copy()
            new_chunk["content"] = truncated + "..."
            new_chunk["token_count"] = TokenBudgetManager.count_tokens(new_chunk["content"])
            return new_chunk

        # Score sentences
        query_words = set(re.findall(r'\w+', query.lower())) if query else set()
        scored_sentences = []
        
        for idx, sentence in enumerate(sentences):
            score = 0.0
            # Boost based on query term matches
            words = re.findall(r'\w+', sentence.lower())
            matches = [w for w in words if w in query_words]
            if words:
                score += (len(matches) / len(words)) * 10.0
            
            # Position boost (first sentence in paragraphs or introductory sentence)
            if idx == 0:
                score += 2.0
            elif idx == len(sentences) - 1:
                score += 1.0
                
            scored_sentences.append((idx, sentence, score))

        # Sort sentences by score descending
        scored_sentences.sort(key=lambda x: x[2], reverse=True)
        
        # Add sentences back in original order until budget is reached
        kept_indices = []
        current_tokens = 0
        
        for idx, sentence, score in scored_sentences:
            sent_tokens = TokenBudgetManager.count_tokens(sentence)
            if current_tokens + sent_tokens <= target_tokens:
                kept_indices.append(idx)
                current_tokens += sent_tokens
            if current_tokens >= target_tokens:
                break
                
        if not kept_indices:
            # Fallback to first sentence
            kept_indices = [0]
            
        kept_indices.sort()
        compressed_text = "... ".join(sentences[i] for i in kept_indices)
        
        new_chunk = chunk.copy()
        new_chunk["content"] = compressed_text
        new_chunk["token_count"] = current_tokens
        new_chunk["is_compressed"] = True
        return new_chunk
