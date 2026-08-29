from typing import List, Set
from app.agents.planning.graph import ExecutionGraph, ExecutionNode

class PlanScheduler:
    @staticmethod
    def get_execution_batches(graph: ExecutionGraph) -> List[List[ExecutionNode]]:
        """Splits the graph nodes into sequential batches that can be executed in parallel."""
        batches = []
        visited: Set[str] = set()
        
        while len(visited) < len(graph.nodes):
            current_batch = []
            for nid, node in graph.nodes.items():
                if nid in visited:
                    continue
                
                # Check if all dependencies of this node are already in 'visited'
                deps_met = True
                for dep_id in node.dependencies:
                    if dep_id not in visited:
                        deps_met = False
                        break
                        
                if deps_met:
                    current_batch.append(node)
            
            if not current_batch:
                # Loop detection safety fallback (should be caught by optimizer)
                break
                
            batches.append(current_batch)
            for node in current_batch:
                visited.add(node.id)
                
        return batches
