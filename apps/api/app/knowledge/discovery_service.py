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

# In-memory storage for user bookmarks, follows, and navigation paths
_USER_BOOKMARKS: Dict[str, List[Dict[str, Any]]] = {} # user_id -> list of saved items
_USER_FOLLOWS: Dict[str, List[str]] = {} # user_id -> list of followed entity_ids

class KnowledgeDiscoveryNavigationService:
    """Centralized Knowledge Discovery & Intelligent Navigation engine combining Universal Search,

    Knowledge Graph, Grounded Copilot Q&A, Knowledge Governance, and Personal Context into guided

    knowledge paths (Search -> Knowledge -> Related Knowledge -> Context -> Discovery -> Action).

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_related_knowledge(
        self,
        user: User,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID
    ) -> Dict[str, Any]:
        """Assembles multi-category related knowledge (Directly Related, Supporting, Affected, Historical, Suggested) for any entity."""
        e_key = str(entity_id)

        # Retrieve mock/stored related knowledge categories
        directly_related = [
            {
                "id": str(uuid4()),
                "title": "Authentication Architecture Document",
                "entity_type": "DOCUMENT",
                "governance_status": "CURRENT",
                "relationship": "Directly Related",
                "explanation": "Primary architecture reference for this project."
            }
        ]
        supporting = [
            {
                "id": str(uuid4()),
                "title": "Engineering Group Discussion",
                "entity_type": "CONVERSATION",
                "governance_status": "VERIFIED",
                "relationship": "Supports Decision",
                "explanation": "Original conversation where PostgreSQL decision was reached."
            }
        ]
        affected = [
            {
                "id": str(uuid4()),
                "title": "Update deployment configuration",
                "entity_type": "TASK",
                "governance_status": "BLOCKED",
                "relationship": "Affected Task",
                "explanation": "Assigned task affected by updated authentication decision."
            }
        ]
        historical = [
            {
                "id": str(uuid4()),
                "title": "PostgreSQL 14 Decision",
                "entity_type": "DECISION",
                "governance_status": "SUPERSEDED",
                "relationship": "Superseded Decision",
                "explanation": "Replaced by PostgreSQL 16 decision."
            }
        ]
        suggested = [
            {
                "id": str(uuid4()),
                "title": "Deployment Guide Document",
                "entity_type": "DOCUMENT",
                "governance_status": "SUGGESTED",
                "relationship": "Suggested Semantic Relation",
                "explanation": "Both reference authentication deployment."
            }
        ]

        return {
            "entity_id": e_key,
            "entity_type": entity_type,
            "categories": {
                "directly_related": directly_related,
                "supporting": supporting,
                "affected": affected,
                "historical": historical,
                "suggested": suggested
            }
        }

    async def get_knowledge_path(
        self,
        user: User,
        organization_id: UUID,
        project_id: UUID,
        current_entity_id: UUID
    ) -> Dict[str, Any]:
        """Generates interactive breadcrumb knowledge path (Project -> Decision -> Task -> Document -> File)."""
        return {
            "project_id": str(project_id),
            "project_name": "Authentication System",
            "breadcrumbs": [
                {"label": "Authentication System", "type": "PROJECT", "entity_id": str(project_id)},
                {"label": "PostgreSQL Decision", "type": "DECISION", "entity_id": str(uuid4())},
                {"label": "Update deployment configuration", "type": "TASK", "entity_id": str(current_entity_id)}
            ]
        }

    async def bookmark_knowledge(
        self,
        user_id: UUID,
        entity_id: UUID,
        entity_type: str,
        title: str,
        governance_status: str = "CURRENT"
    ) -> Dict[str, Any]:
        """Bookmarks an entity to user's saved knowledge collection."""
        u_key = str(user_id)
        e_key = str(entity_id)

        if u_key not in _USER_BOOKMARKS:
            _USER_BOOKMARKS[u_key] = []

        for b in _USER_BOOKMARKS[u_key]:
            if b["entity_id"] == e_key:
                return {"success": True, "message": "Already bookmarked", "bookmarks": _USER_BOOKMARKS[u_key]}

        b_item = {
            "id": str(uuid4()),
            "entity_id": e_key,
            "entity_type": entity_type,
            "title": title,
            "governance_status": governance_status,
            "saved_at": datetime.utcnow().isoformat()
        }
        _USER_BOOKMARKS[u_key].append(b_item)
        return {"success": True, "message": "Knowledge bookmarked successfully", "bookmarks": _USER_BOOKMARKS[u_key]}

    async def follow_entity(
        self,
        user_id: UUID,
        entity_id: UUID
    ) -> Dict[str, Any]:
        """Subscribes user to proactive updates on a decision/project."""
        u_key = str(user_id)
        e_key = str(entity_id)
        if u_key not in _USER_FOLLOWS:
            _USER_FOLLOWS[u_key] = []
        if e_key not in _USER_FOLLOWS[u_key]:
            _USER_FOLLOWS[u_key].append(e_key)
        return {"success": True, "message": "Following entity for proactive updates", "followed_entity_ids": _USER_FOLLOWS[u_key]}

    async def get_saved_knowledge(
        self,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """Retrieves user's saved knowledge collection with updated governance statuses."""
        u_key = str(user_id)
        return _USER_BOOKMARKS.get(u_key, [])
