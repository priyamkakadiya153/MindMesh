from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field

class AgentExecutionNode(BaseModel):
    id: str
    agent_name: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Dynamic conditional branching predicate
    condition_path: Optional[str] = None  # key in result to check for true/false to skip or take branch

class AgentExecutionGraph(BaseModel):
    nodes: Dict[str, AgentExecutionNode] = Field(default_factory=dict)

    def add_node(self, node: AgentExecutionNode):
        self.nodes[node.id] = node

    def get_ready_nodes(self) -> List[AgentExecutionNode]:
        """Gets all nodes with dependencies completed that are PENDING."""
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
        return all(node.status == "COMPLETED" or node.status == "SKIPPED" for node in self.nodes.values())

    def is_failed(self) -> bool:
        return any(node.status == "FAILED" for node in self.nodes.values())

    def serialize(self) -> Dict[str, Any]:
        return {nid: n.model_dump() for nid, n in self.nodes.items()}
