import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class MemorySummarizer:
    @staticmethod
    def merge_payloads(payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merges multiple JSON objects into a single summary dictionary."""
        merged = {}
        history = []

        for payload in payloads:
            for k, v in payload.items():
                if k == "history" and isinstance(v, list):
                    history.extend(v)
                elif k not in merged:
                    merged[k] = v
                elif isinstance(merged[k], list) and isinstance(v, list):
                    merged[k] = list(set(merged[k] + v))
                elif isinstance(merged[k], dict) and isinstance(v, dict):
                    merged[k] = {**merged[k], **v}
                else:
                    # Keep latest value
                    merged[k] = v

        if history:
            # Sort/limit history elements
            merged["history"] = history[-10:]

        merged["consolidated_at"] = datetime_str = "" # placeholder metadata update
        return merged
