import logging
from typing import Dict, List, Optional
from app.agents.context import SessionContext
from app.agents.sdk.session import AgentSession
from app.agents.exceptions import SessionException

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self):
        self._sessions: Dict[str, AgentSession] = {}

    def create_session(self, context: SessionContext) -> AgentSession:
        """Creates and tracks a new execution session."""
        session_id = context.request_id
        if session_id in self._sessions:
            raise SessionException(f"Session with request ID '{session_id}' already exists.")
            
        session = AgentSession(context)
        self._sessions[session_id] = session
        logger.info(f"Created agent session {session_id}")
        return session

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Look up session by ID."""
        return self._sessions.get(session_id)

    def list_sessions(self) -> List[AgentSession]:
        """List all active/tracked sessions."""
        return list(self._sessions.values())

    def clear_sessions(self):
        """Clears session cache."""
        self._sessions.clear()

# Global manager instance
agent_manager = AgentManager()
