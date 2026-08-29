from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, List
from app.agents.context import SessionContext

class AgentSession:
    def __init__(self, context: SessionContext):
        self.session_id = context.request_id or str(uuid4())
        self.context = context
        self.start_time = datetime.utcnow()
        self.end_time = None
        self.status = "CREATED"
        self.logs: List[Dict[str, Any]] = []
        self.result = None
        self.error = None

    def log(self, level: str, msg: str):
        self.logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": msg
        })

    def complete(self, result: Dict[str, Any]):
        self.end_time = datetime.utcnow()
        self.status = "COMPLETED"
        self.result = result

    def fail(self, error: Exception):
        self.end_time = datetime.utcnow()
        self.status = "FAILED"
        self.error = str(error)

    def duration_ms(self) -> float:
        end = self.end_time or datetime.utcnow()
        return (end - self.start_time).total_seconds() * 1000.0
