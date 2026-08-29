import re
from typing import List, Dict, Any
from app.agents.planning.graph import ExecutionNode

class DependencyResolver:
    @staticmethod
    def resolve_dependencies(tasks_data: List[Dict[str, Any]]) -> List[ExecutionNode]:
        """Resolves dependencies by parsing dynamic input parameters (e.g. ${step_1.result.id})."""
        nodes = []
        for task in tasks_data:
            node_id = task["id"]
            tool = task["tool"]
            inputs = task.get("input", {})
            dependencies = list(task.get("dependencies", []))

            # Scan inputs for template patterns: ${step_id.result.field}
            dep_pattern = re.compile(r"\$\{\s*([a-zA-Z0-9_-]+)\.result\.[a-zA-Z0-9_-]+\s*\}")
            
            def scan_value(val: Any):
                if isinstance(val, str):
                    match = dep_pattern.search(val)
                    if match:
                        parent_id = match.group(1)
                        if parent_id not in dependencies:
                            dependencies.append(parent_id)
                elif isinstance(val, dict):
                    for k, v in val.items():
                        scan_value(v)
                elif isinstance(val, list):
                    for item in val:
                        scan_value(item)

            for key, val in inputs.items():
                scan_value(val)

            nodes.append(ExecutionNode(
                id=node_id,
                tool=tool,
                input=inputs,
                dependencies=dependencies,
                status="PENDING"
            ))
        return nodes
