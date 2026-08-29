import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OrchestrationMetrics:
    def __init__(self):
        self.coordination_latencies = []
        self.agent_utilization: Dict[str, int] = {}
        self.conflicts_count = 0
        self.consensus_verifications = 0

    def record_coordination(self, latency_ms: float):
        self.coordination_latencies.append(latency_ms)

    def record_agent_call(self, agent_name: str):
        self.agent_utilization[agent_name] = self.agent_utilization.get(agent_name, 0) + 1

    def record_conflict(self):
        self.conflicts_count += 1

    def record_consensus(self):
        self.consensus_verifications += 1

    def get_summary(self) -> Dict[str, Any]:
        avg_latency = (sum(self.coordination_latencies) / len(self.coordination_latencies)) if self.coordination_latencies else 0.0
        return {
            "avg_coordination_latency_ms": round(avg_latency, 2),
            "agent_utilization": self.agent_utilization,
            "conflicts_resolved": self.conflicts_count,
            "consensus_verifications": self.consensus_verifications
        }

orchestration_metrics = OrchestrationMetrics()
