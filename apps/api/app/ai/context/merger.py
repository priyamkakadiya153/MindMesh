from typing import List, Dict, Any

class ChunkMerger:
    @staticmethod
    def merge_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merges duplicate and contiguous/adjacent document chunks.
        
        Args:
            chunks: A list of retrieved chunk dictionaries. Each chunk must contain at least:
                - document_id
                - content
                - score
                - page (int, optional)
                - chunk_index (int, optional)
        """
        if not chunks:
            return []
            
        # 1. Deduplicate by unique chunk identifier or exact content matching
        seen_chunks = set()
        deduplicated = []
        for c in chunks:
            # Create a unique key for deduplication
            key = c.get("chunk_id") or hash(c["content"])
            if key not in seen_chunks:
                seen_chunks.add(key)
                deduplicated.append(c)
                
        # 2. Group by document
        by_doc: Dict[str, List[Dict[str, Any]]] = {}
        for c in deduplicated:
            doc_id = str(c.get("document_id") or "unknown")
            by_doc.setdefault(doc_id, []).append(c)
            
        merged_results = []
        for doc_id, doc_chunks in by_doc.items():
            if not doc_chunks:
                continue
                
            # If doc chunks can be sorted by index, do that. Otherwise sort by page
            # We want to check chunk_index or page
            doc_chunks.sort(key=lambda x: (x.get("page") or 1, x.get("chunk_index") or 0))
            
            current_merged = doc_chunks[0].copy()
            
            for next_chunk in doc_chunks[1:]:
                # Heuristic: Check if adjacent by chunk_index, or page similarity, or text overlap
                is_contiguous = False
                
                curr_idx = current_merged.get("chunk_index")
                next_idx = next_chunk.get("chunk_index")
                if curr_idx is not None and next_idx is not None:
                    if next_idx == curr_idx + 1:
                        is_contiguous = True
                else:
                    # If index is not available, check if same page
                    curr_page = current_merged.get("page")
                    next_page = next_chunk.get("page")
                    if curr_page == next_page:
                        is_contiguous = True
                        
                if is_contiguous:
                    # Merge content: check for text overlap or simple newline separation
                    c1_text = current_merged["content"]
                    c2_text = next_chunk["content"]
                    
                    # Remove minor overlap if any (simple suffix/prefix match check up to 100 chars)
                    overlap_len = 0
                    max_overlap = min(len(c1_text), len(c2_text), 100)
                    for i in range(max_overlap, 0, -1):
                        if c1_text.endswith(c2_text[:i]):
                            overlap_len = i
                            break
                            
                    if overlap_len > 0:
                        merged_content = c1_text + c2_text[overlap_len:]
                    else:
                        merged_content = c1_text + "\n\n" + c2_text
                        
                    current_merged["content"] = merged_content
                    # Take the maximum score (relevance) or average. Let's take maximum
                    current_merged["score"] = max(current_merged.get("score", 0), next_chunk.get("score", 0))
                    # Merge metadata pages/indices if different
                    if next_chunk.get("page") and next_chunk.get("page") != current_merged.get("page"):
                        # Keep list of pages or range
                        if "pages" not in current_merged:
                            current_merged["pages"] = [current_merged.get("page"), next_chunk.get("page")]
                        else:
                            current_merged["pages"].append(next_chunk.get("page"))
                else:
                    merged_results.append(current_merged)
                    current_merged = next_chunk.copy()
                    
            merged_results.append(current_merged)
            
        # Sort final results by score descending
        merged_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return merged_results
