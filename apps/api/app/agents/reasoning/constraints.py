from app.agents.exceptions import AgentException

class ConstraintValidator:
    @staticmethod
    def check_loop_limit(execution_count: int, max_limit: int = 20):
        """Raises exception if step execution depth count exceeds threshold."""
        if execution_count > max_limit:
            raise AgentException(
                f"Execution aborted: Agent execution loop limit reached ({execution_count} runs). Potential loop detected."
            )

    @staticmethod
    def check_cost_limits(estimated_cost: float, max_cost: float = 5.0):
        """Raises exception if estimated plan execution cost exceeds limits."""
        if estimated_cost > max_cost:
            raise AgentException(
                f"Execution aborted: Estimated execution cost (${estimated_cost}) exceeds budget limit (${max_cost})."
            )
