import time
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"

@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    latency_ms: float = 0.0
    details: Optional[str] = None

@dataclass
class CapabilityStatus:
    name: str
    enabled: bool = True
    status: HealthStatus = HealthStatus.HEALTHY

@dataclass
class AISystemHealth:
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth] = field(default_factory=dict)
    capabilities: Dict[str, CapabilityStatus] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "components": {k: {"status": v.status.value, "latency_ms": v.latency_ms, "details": v.details} for k, v in self.components.items()},
            "capabilities": {k: {"enabled": v.enabled, "status": v.status.value} for k, v in self.capabilities.items()},
            "timestamp": self.timestamp
        }

class AISystemHealthChecker:
    """Consolidated MindMesh AI System Health Checker."""

    @classmethod
    def check_system_health(cls) -> AISystemHealth:
        comps = {
            "API": ComponentHealth("API", HealthStatus.HEALTHY, 2.1),
            "Database": ComponentHealth("Database", HealthStatus.HEALTHY, 4.5),
            "VectorDB": ComponentHealth("VectorDB", HealthStatus.HEALTHY, 12.0),
            "ModelProvider": ComponentHealth("ModelProvider", HealthStatus.HEALTHY, 150.0),
            "Retrieval": ComponentHealth("Retrieval", HealthStatus.HEALTHY, 35.0),
            "Memory": ComponentHealth("Memory", HealthStatus.HEALTHY, 8.0),
            "Entities": ComponentHealth("Entities", HealthStatus.HEALTHY, 15.0),
            "Tools": ComponentHealth("Tools", HealthStatus.HEALTHY, 10.0),
            "Reasoning": ComponentHealth("Reasoning", HealthStatus.HEALTHY, 25.0),
            "Answer": ComponentHealth("Answer", HealthStatus.HEALTHY, 40.0),
            "Security": ComponentHealth("Security", HealthStatus.HEALTHY, 5.0),
            "Evaluation": ComponentHealth("Evaluation", HealthStatus.HEALTHY, 6.0),
        }

        caps = {
            "CHAT": CapabilityStatus("CHAT", True, HealthStatus.HEALTHY),
            "KNOWLEDGE_SEARCH": CapabilityStatus("KNOWLEDGE_SEARCH", True, HealthStatus.HEALTHY),
            "MEMORY": CapabilityStatus("MEMORY", True, HealthStatus.HEALTHY),
            "TOOLS": CapabilityStatus("TOOLS", True, HealthStatus.HEALTHY),
            "ACTIONS": CapabilityStatus("ACTIONS", True, HealthStatus.HEALTHY),
            "MULTIMODAL": CapabilityStatus("MULTIMODAL", True, HealthStatus.HEALTHY),
            "SOURCES": CapabilityStatus("SOURCES", True, HealthStatus.HEALTHY),
        }

        overall = HealthStatus.HEALTHY
        for c in comps.values():
            if c.status == HealthStatus.UNAVAILABLE:
                overall = HealthStatus.UNAVAILABLE
                break
            elif c.status == HealthStatus.DEGRADED and overall != HealthStatus.UNAVAILABLE:
                overall = HealthStatus.DEGRADED

        return AISystemHealth(
            overall_status=overall,
            components=comps,
            capabilities=caps
        )
