import logging
from typing import List, Tuple, Callable, Dict

logger = logging.getLogger(__name__)

class MultiAgentRollbackTracker:
    def __init__(self):
        self._actions: List[Tuple[str, Callable, Tuple, Dict]] = []

    def register_rollback(self, step_name: str, func: Callable, *args, **kwargs):
        """Registers a compensating rollback callback."""
        self._actions.append((step_name, func, args, kwargs))
        logger.info(f"MultiAgentRollbackTracker: Registered compensation for agent step '{step_name}'")

    async def execute_rollback(self):
        """Executes all compensating callbacks in reverse order."""
        if not self._actions:
            return

        logger.warning(f"MultiAgentRollbackTracker: Executing {len(self._actions)} compensations...")
        for step_name, func, args, kwargs in reversed(self._actions):
            try:
                logger.info(f"MultiAgentRollbackTracker: Reverting changes for step '{step_name}'...")
                await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"MultiAgentRollbackTracker: Failed to revert step '{step_name}': {str(e)}",
                    exc_info=True
                )
        self._actions.clear()

# Compatibility shim for existing imports
class RollbackManager(MultiAgentRollbackTracker):
    """Compatibility wrapper for legacy imports.
    Inherits all behavior from MultiAgentRollbackTracker.
    """
    pass

__all__ = ["MultiAgentRollbackTracker", "RollbackManager"]
