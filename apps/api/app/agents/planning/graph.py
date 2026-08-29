from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class ExecutionNode(BaseModel):
    id: str
    tool: str
    input: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result: Optional[Any] = None
    error: Optional[str] = None
    retries: int = 0

class ExecutionGraph(BaseModel):
    nodes: Dict[str, ExecutionNode] = Field(default_factory=dict)

    def add_node(self, node: ExecutionNode):
        self.nodes[node.id] = node

    def get_ready_nodes(self) -> List[ExecutionNode]:
        """Gets all nodes with all dependencies met that have PENDING status."""
        ready = []
        for node in self.nodes.values():
            if node.status != "PENDING":
                continue
            
            # Check dependencies
            deps_met = True
            for dep_id in node.dependencies:
                dep_node = self.nodes.get(dep_id)
                if not dep_node or dep_node.status != "COMPLETED":
                    deps_met = False
                    break
            
            if deps_met:
                ready.append(node)
        return ready

    def is_completed(self) -> bool:
        """Returns True if all nodes are COMPLETED."""
        return all(node.status == "COMPLETED" for node in self.nodes.values())

    def is_failed(self) -> bool:
        """Returns True if any node is FAILED."""
        return any(node.status == "FAILED" for node in self.nodes.values())

    def serialize(self) -> Dict[str, Any]:
        return {nid: n.model_dump() for nid, n in self.nodes.items()}

    @classmethod
    def deserialize(cls, data: Dict[str, Any]) -> "ExecutionGraph":
        graph = cls()
        for nid, val in data.items():
            graph.add_node(ExecutionNode(**val))
        return graph
