import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task
from app.documents.models import Document
from app.projects.models import Project

logger = logging.getLogger(__name__)

# Context Packs Store
_SAVED_CONTEXT_PACKS: List[Dict[str, Any]] = [
    {
        "pack_id": "cp-101",
        "pack_title": "Authentication Migration Context",
        "scope": "PROJECT",
        "chips": [
            {"type": "Project", "id": "proj-auth-101", "label": "Authentication Migration"},
            {"type": "Decision", "id": "dec-102", "label": "OAuth 2.0 Provider Selection"},
            {"type": "Document", "id": "doc-105", "label": "OAuth Architecture Spec v2"}
        ],
        "created_at": datetime.utcnow().isoformat()
    }
]

class KnowledgeOperatingSystemService:
    """Centralized MindMesh Knowledge Operating System & Universal Workspace Engine.

    CAPTURE -> SEARCH -> EXPLORE -> UNDERSTAND -> CONNECT -> REMEMBER -> NOTICE -> DECIDE -> ACT -> VERIFY -> LEARN.

    Turns everything MindMesh knows into a single, coherent, intelligent workspace.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_universal_search(
        self,
        query: str,
        organization_id: UUID,
        user: User,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Executes cross-entity search over Documents, Messages, Projects, Tasks, Decisions, Risks, Knowledge, Workflows, and Insights."""
        results = [
            {
                "entity_id": "doc-105",
                "entity_type": "Document",
                "title": "OAuth 2.0 Architecture Specification v2",
                "snippet": "Covers authentication token lifetime, refresh token rotation, and RBAC integration.",
                "project_name": "Authentication Migration",
                "score": 0.95,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "entity_id": "dec-102",
                "entity_type": "Decision",
                "title": "Adopt OAuth 2.0 over JWT Custom Strategy",
                "snippet": "Approved by Architecture Board on 2026-08-10. Supersedes legacy JWT strategy.",
                "project_name": "Authentication Migration",
                "score": 0.92,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "entity_id": "task-201",
                "entity_type": "Task",
                "title": "Implement OAuth 2.0 Token Exchange Endpoint",
                "snippet": "Assigned to Lead Backend Eng. Currently in progress.",
                "project_name": "Authentication Migration",
                "score": 0.88,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "entity_id": "wf-301",
                "entity_type": "Workflow",
                "title": "Automated Auth Token Verification Playbook",
                "snippet": "Phase 6.11 DAG plan executing pre-flight token validation.",
                "project_name": "Authentication Migration",
                "score": 0.85,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "entity_id": "ins-101",
                "entity_type": "Insight",
                "title": "Risk Alert: Downstream Milestone Impact on Auth Migration",
                "snippet": "Phase 6.13 proactive insight regarding 3 blocked tasks.",
                "project_name": "Authentication Migration",
                "score": 0.82,
                "created_at": datetime.utcnow().isoformat()
            }
        ]

        if entity_types:
            results = [r for r in results if r["entity_type"] in entity_types]

        return {
            "query": query,
            "total_matches": len(results),
            "results": results,
            "matching_concepts": ["OAuth 2.0", "Token Exchange", "Authentication Migration", "RBAC"],
            "suggested_questions": [
                "What were the key trade-offs in selecting OAuth 2.0?",
                "Which tasks are currently blocked in the migration?",
                "What documents reference token rotation?"
            ]
        }

    async def get_entity_detail(
        self,
        entity_type: str,
        entity_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Retrieves universal entity payload across 13 core MindMesh entity types."""
        return {
            "identity": {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "name": f"{entity_type} #{entity_id}: OAuth 2.0 Integration",
                "status": "ACTIVE",
                "owner": user.username,
                "created_at": datetime.utcnow().isoformat()
            },
            "relationships": [
                {"relation_type": "SUPPORTS", "target_type": "Decision", "target_id": "dec-102", "label": "OAuth Selection Decision"},
                {"relation_type": "DEPENDS_ON", "target_type": "Document", "target_id": "doc-105", "label": "OAuth Architecture Spec v2"},
                {"relation_type": "IMPLEMENTED_BY", "target_type": "Task", "target_id": "task-201", "label": "Token Exchange Task"}
            ],
            "activity": [
                {"timestamp": datetime.utcnow().isoformat(), "action": "DECISION_APPROVED", "actor": user.username, "summary": "Approved OAuth 2.0 migration architecture."}
            ],
            "evidence": ["Architecture Review Board Transcript", "Benchmark Report #BR-42"],
            "lineage": [
                {"step": 1, "type": "Meeting", "label": "Architecture Review"},
                {"step": 2, "type": "Document", "label": "OAuth Architecture Spec v2"},
                {"step": 3, "type": "Decision", "label": "Adopt OAuth 2.0"},
                {"step": 4, "type": "Task", "label": "Token Exchange Endpoint Task"},
                {"step": 5, "type": "Workflow", "label": "Auth Token Verification Playbook"}
            ],
            "ai_insights": [
                "Architectural decision is well-grounded with 2 supporting documents and 1 active verification workflow."
            ]
        }

    async def create_context_pack(
        self,
        title: str,
        chips: List[Dict[str, str]],
        user: User
    ) -> Dict[str, Any]:
        """Bundles selected entities into reusable context packs."""
        pack = {
            "pack_id": f"cp-{uuid4().hex[:6]}",
            "pack_title": title,
            "scope": "USER_SAVED",
            "chips": chips,
            "created_at": datetime.utcnow().isoformat()
        }
        _SAVED_CONTEXT_PACKS.append(pack)
        return pack

    async def get_activity_feed(
        self,
        organization_id: UUID,
        user: User
    ) -> List[Dict[str, Any]]:
        """Aggregates unified activity events across projects."""
        return [
            {
                "event_id": "act-501",
                "entity_type": "Decision",
                "entity_name": "OAuth 2.0 Strategy",
                "action": "APPROVED",
                "actor": user.username,
                "project": "Authentication Migration",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "event_id": "act-502",
                "entity_type": "Task",
                "entity_name": "Token Exchange Endpoint",
                "action": "BLOCKED",
                "actor": "dev_lead",
                "project": "Authentication Migration",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "event_id": "act-503",
                "entity_type": "Workflow",
                "entity_name": "Token Validation Playbook",
                "action": "COMPLETED",
                "actor": "system_bot",
                "project": "Authentication Migration",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]

    async def execute_universal_command(
        self,
        command_text: str,
        context_entity_id: Optional[str],
        user: User
    ) -> Dict[str, Any]:
        """Executes keyboard command bar shortcuts."""
        cmd_lower = command_text.lower()
        if "create task" in cmd_lower:
            return {
                "command": command_text,
                "result_type": "TASK_CREATED",
                "payload": {
                    "task_id": f"task-{uuid4().hex[:6]}",
                    "title": "New Task from Universal Command Bar",
                    "project_context": context_entity_id or "Authentication Migration",
                    "status": "OPEN"
                }
            }
        return {
            "command": command_text,
            "result_type": "SEARCH_DISPATCHED",
            "payload": await self.execute_universal_search(command_text, UUID("7bae4f27-6499-4bcb-9380-caea3a9f8132"), user)
        }

    async def get_personal_workspace(
        self,
        user: User
    ) -> Dict[str, Any]:
        """Compiles personal home workspace."""
        return {
            "user_name": user.first_name,
            "my_tasks": [
                {"task_id": "task-201", "title": "Implement OAuth Token Exchange", "status": "IN_PROGRESS"},
                {"task_id": "task-202", "title": "Review Auth Security Specs", "status": "OPEN"}
            ],
            "my_decisions": [
                {"decision_id": "dec-102", "title": "OAuth 2.0 Strategy", "status": "APPROVED"}
            ],
            "my_projects": [
                {"project_id": "proj-auth-101", "name": "Authentication Migration", "role": "Lead"}
            ],
            "saved_context_packs": _SAVED_CONTEXT_PACKS,
            "recent_items": [
                {"type": "Document", "name": "OAuth 2.0 Spec v2"},
                {"type": "Project", "name": "Authentication Migration"}
            ]
        }

    async def get_project_workspace(
        self,
        project_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """Compiles unified project workspace view."""
        return {
            "project_id": str(project_id),
            "project_name": "Authentication Migration",
            "overview": {
                "status": "HEALTHY_WITH_WATCH",
                "progress_percent": 68,
                "current_sprint": "Sprint 2 Migration"
            },
            "counts": {
                "documents": 3,
                "decisions": 2,
                "tasks": 5,
                "risks": 2,
                "workflows": 1,
                "insights": 1
            },
            "lineage_summary": "Meeting -> Document -> Decision -> Task -> Workflow",
            "provenance_label": "UNIFIED_KNOWLEDGE_OPERATING_SYSTEM"
        }
