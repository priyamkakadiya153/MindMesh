import logging
from datetime import datetime
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

class SearchAnalyticsTracker:
    def __init__(self):
        self._logs = []

    def record_search(
        self,
        query: str,
        duration_ms: float,
        result_count: int,
        user_id: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> None:
        """Records a search query execution event logs details."""
        log_entry = {
            "query": query,
            "duration_ms": duration_ms,
            "result_count": result_count,
            "user_id": user_id,
            "workspace_id": workspace_id,
            "timestamp": datetime.utcnow(),
            "clicks": []
        }
        self._logs.append(log_entry)
        logger.info(f"Analytics - Search: '{query}', Results: {result_count}, Latency: {duration_ms:.1f}ms")

    def record_click(self, query: str, document_id: str) -> None:
        """Records document click action for a query."""
        for log in reversed(self._logs):
            if log["query"] == query:
                log["clicks"].append(document_id)
                logger.info(f"Analytics - Click: '{query}' -> Doc: {document_id}")
                break

    def get_popular_queries(self, limit: int = 10) -> List[Dict]:
        """Returns most frequently executed search terms list."""
        counts = {}
        for log in self._logs:
            q = log["query"]
            counts[q] = counts.get(q, 0) + 1
            
        sorted_queries = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"query": q, "count": count} for q, count in sorted_queries[:limit]]

    def get_zero_result_queries(self, limit: int = 10) -> List[Dict]:
        """Returns queries that returned zero matches count."""
        counts = {}
        for log in self._logs:
            if log["result_count"] == 0:
                q = log["query"]
                counts[q] = counts.get(q, 0) + 1
                
        sorted_queries = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        return [{"query": q, "count": count} for q, count in sorted_queries[:limit]]

    def get_recent_history(self, user_id: str, limit: int = 10) -> List[str]:
        """Returns unique recent queries history executed by a user."""
        queries = []
        for log in reversed(self._logs):
            if log.get("user_id") == str(user_id):
                q = log["query"]
                if q not in queries:
                    queries.append(q)
                if len(queries) >= limit:
                    break
        return queries

analytics_tracker = SearchAnalyticsTracker()
