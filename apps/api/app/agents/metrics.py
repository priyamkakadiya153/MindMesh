import time
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AgentMetricsTracker:
    def __init__(self):
        self.executions = 0
        self.successes = 0
        self.failures = 0
        self.total_time_ms = 0.0
        self.agent_stats: Dict[str, Dict[str, Any]] = {}
        self.tool_calls: Dict[str, int] = {}

    def record_execution(self, agent_id: str, duration_ms: float, success: bool):
        self.executions += 1
        if success:
            self.successes += 1
        else:
            self.failures += 1
        self.total_time_ms += duration_ms

        # Agent-specific metrics
        if agent_id not in self.agent_stats:
            self.agent_stats[agent_id] = {
                "executions": 0,
                "successes": 0,
                "failures": 0,
                "total_time_ms": 0.0
            }
        
        stats = self.agent_stats[agent_id]
        stats["executions"] += 1
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1
        stats["total_time_ms"] += duration_ms

        logger.info(
            f"AgentMetrics: '{agent_id}' execution took {duration_ms:.2f}ms. Status: {'SUCCESS' if success else 'FAILED'}"
        )

    def record_tool_call(self, tool_name: str):
        self.tool_calls[tool_name] = self.tool_calls.get(tool_name, 0) + 1

    def get_metrics_summary(self) -> Dict[str, Any]:
        avg_latency = (self.total_time_ms / self.executions) if self.executions > 0 else 0.0
        return {
            "total_executions": self.executions,
            "successes": self.successes,
            "failures": self.failures,
            "failure_rate": (self.failures / self.executions) if self.executions > 0 else 0.0,
            "avg_latency_ms": round(avg_latency, 2),
            "agents": {
                aid: {
                    "executions": s["executions"],
                    "success_rate": (s["successes"] / s["executions"]) if s["executions"] > 0 else 0.0,
                    "avg_latency_ms": round(s["total_time_ms"] / s["executions"], 2) if s["executions"] > 0 else 0.0
                }
                for aid, s in self.agent_stats.items()
            },
            "tool_calls": self.tool_calls
        }

metrics_tracker = AgentMetricsTracker()
