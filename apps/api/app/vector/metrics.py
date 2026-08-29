from typing import Dict, Any

class VectorMetricsManager:
    def __init__(self):
        self._metrics = {
            "total_vectors": 0,
            "active_indexes": 0,
            "query_latency_ms": 0.0,
            "insert_rate": 0.0,
            "delete_rate": 0.0,
            "index_size_bytes": 0,
            "cache_hit_rate": 1.0,
            "failed_jobs": 0,
            "search_count": 0,
            "total_search_latency_ms": 0.0,
            "insert_count": 0,
            "delete_count": 0,
            "rebuild_durations": []
        }

    def record_search(self, latency_ms: float):
        self._metrics["search_count"] += 1
        self._metrics["total_search_latency_ms"] += latency_ms
        self._metrics["query_latency_ms"] = (
            self._metrics["total_search_latency_ms"] / self._metrics["search_count"]
        )

    def record_insert(self, count: int = 1):
        self._metrics["insert_count"] += count
        self._metrics["total_vectors"] += count

    def record_delete(self, count: int = 1):
        self._metrics["delete_count"] += count
        self._metrics["total_vectors"] = max(0, self._metrics["total_vectors"] - count)

    def record_failed_job(self):
        self._metrics["failed_jobs"] += 1

    def record_rebuild(self, duration_s: float):
        self._metrics["rebuild_durations"].append(duration_s)

    def get_metrics(self) -> Dict[str, Any]:
        return dict(self._metrics)

metrics_manager = VectorMetricsManager()
