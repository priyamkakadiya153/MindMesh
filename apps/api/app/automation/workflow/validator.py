import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class WorkflowValidator:
    @staticmethod
    def validate_definition(definition: Dict[str, Any]) -> List[str]:
        """Validates workflow step names, trigger types, policies, and catches cycle dependency loops.

        Returns a list of error message strings. If empty, validation is successful.
        """
        errors = []

        if not isinstance(definition, dict):
            return ["Workflow definition must be a JSON/YAML object."]

        # Validate trigger
        trigger = definition.get("trigger", {})
        trigger_type = trigger.get("type")
        if not trigger_type:
            errors.append("Workflow triggers must define a 'type' (event, schedule, manual).")
        elif trigger_type not in ["event", "schedule", "manual"]:
            errors.append(f"Invalid trigger type '{trigger_type}'. Allowed: event, schedule, manual.")

        # Validate steps
        steps = definition.get("steps")
        if not steps or not isinstance(steps, list):
            errors.append("Workflow must contain a non-empty list of 'steps'.")
            return errors

        step_names = set()
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                errors.append(f"Step at index {idx} must be a dictionary.")
                continue

            name = step.get("name")
            if not name:
                errors.append(f"Step at index {idx} is missing required 'name' field.")
            else:
                if name in step_names:
                    errors.append(f"Duplicate step name '{name}' detected.")
                step_names.add(name)

            step_type = step.get("type")
            if not step_type:
                errors.append(f"Step '{name or idx}' is missing required 'type' field.")
            elif step_type not in ["sequential", "parallel", "conditional", "human_approval", "ai_agent", "notification", "http_api"]:
                errors.append(f"Invalid step type '{step_type}' in step '{name or idx}'.")

        # Validate dependency checks to prevent cyclic/deadlock paths
        for idx, step in enumerate(steps):
            deps = step.get("dependencies", [])
            for dep in deps:
                if dep not in step_names:
                    errors.append(f"Step '{step.get('name', idx)}' references undefined dependency step '{dep}'.")

        # Cycle detection
        visited = {}
        def has_cycle(node: str) -> bool:
            visited[node] = 1 # processing
            # Find dependents
            deps = []
            for step in steps:
                if step.get("name") == node:
                    deps = step.get("dependencies", [])
                    break
            for dep in deps:
                if visited.get(dep) == 1:
                    return True
                if visited.get(dep) != 2:
                    if has_cycle(dep):
                        return True
            visited[node] = 2 # processed
            return False

        for name in step_names:
            if visited.get(name) != 2:
                if has_cycle(name):
                    errors.append("Cyclic dependency loop detected among workflow steps.")
                    break

        return errors
