import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AgentTeamLifecycle:
    def __init__(self):
        self.active_teams: Dict[str, Dict[str, Any]] = {}

    def register_team(self, execution_id: str, supervisor_name: str):
        self.active_teams[execution_id] = {
            "supervisor": supervisor_name,
            "status": "RUNNING",
            "active_agents": []
        }
        logger.info(f"AgentTeamLifecycle: Registered active team for execution {execution_id}")

    def update_agent_state(self, execution_id: str, agent_name: str, status: str):
        team = self.active_teams.get(execution_id)
        if team:
            if status == "RUNNING" and agent_name not in team["active_agents"]:
                team["active_agents"].append(agent_name)
            elif status in ["COMPLETED", "FAILED"] and agent_name in team["active_agents"]:
                team["active_agents"].remove(agent_name)

    def teardown_team(self, execution_id: str, success: bool = True):
        if execution_id in self.active_teams:
            self.active_teams[execution_id]["status"] = "COMPLETED" if success else "FAILED"
            self.active_teams[execution_id]["active_agents"].clear()
            logger.info(f"AgentTeamLifecycle: Teardown completed for execution {execution_id}")

agent_lifecycle = AgentTeamLifecycle()
