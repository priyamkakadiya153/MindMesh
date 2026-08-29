import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PlanningMetricsTracker:
    def __init__(self):
        self.plans_generated = 0
        self.total_steps_planned = 0
        self.planning_latencies = []

    def record_plan(self, graph_size: int, duration_ms: float):
        self.plans_generated += 1
        self.total_steps_planned += graph_size
        self.planning_latencies.append(duration_ms)
        
        logger.info(
            f"PlanningMetrics: Generated plan with {graph_size} steps in {duration_ms:.2f}ms."
        )

    def get_summary(self) -> Dict[str, Any]:
        avg_latency = (sum(self.planning_latencies) / len(self.planning_latencies)) if self.planning_latencies else 0.0
        return {
            "plans_generated": self.plans_generated,
            "total_steps_planned": self.total_steps_planned,
            "avg_planning_latency_ms": round(avg_latency, 2)
        }

planning_metrics = PlanningMetricsTracker()
