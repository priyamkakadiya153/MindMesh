import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ResultAggregator:
    @staticmethod
    def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merges outputs from multiple agents into a unified structure, removing duplicates."""
        merged_synthesis = []
        merged_search_results = []
        citations_seen = set()
        merged_citations = []
        metadata_summary = {}

        for res in results:
            if not isinstance(res, dict):
                continue
            
            # Aggregate textual synthesis/messages
            synth = res.get("synthesis") or res.get("message")
            if synth:
                merged_synthesis.append(synth)
                
            # Aggregate search results/documents
            search_items = res.get("search_results") or res.get("data")
            if isinstance(search_items, list):
                for item in search_items:
                    if isinstance(item, dict):
                        doc_id = item.get("id") or item.get("name")
                        if doc_id and doc_id not in citations_seen:
                            citations_seen.add(doc_id)
                            merged_search_results.append(item)
                            merged_citations.append({
                                "id": doc_id,
                                "title": item.get("title", item.get("name", "Document Reference")),
                                "score": item.get("score", 1.0)
                            })
            elif isinstance(search_items, dict):
                merged_search_results.append(search_items)

            # Aggregate custom KV metadata keys
            for k, val in res.items():
                if k not in ["synthesis", "message", "search_results", "data", "citations"]:
                    metadata_summary[k] = val

        return {
            "synthesis": "\n\n".join(merged_synthesis) if merged_synthesis else "Multi-agent task completed successfully.",
            "search_results": merged_search_results,
            "citations": merged_citations,
            "metadata": metadata_summary
        }
