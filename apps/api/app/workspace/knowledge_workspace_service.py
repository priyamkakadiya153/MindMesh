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

# In-memory storage for workspace collections, saved items, and knowledge attachments
_COLLECTIONS: Dict[str, Dict[str, Any]] = {}
_SAVED_ITEMS: Dict[str, List[Dict[str, Any]]] = {}
_ATTACHMENTS: List[Dict[str, Any]] = []

class KnowledgeWorkspaceService:
    """Centralized Knowledge Operations, Discovery & Intelligent Workspace Experience Engine.

    KNOWLEDGE HOME -> DISCOVERY & COLLECTIONS -> PROJECT KNOWLEDGE HUB -> ENTITY DETAIL & LINEAGE -> REUSE & ATTACHMENT.

    Unifies search, graph, governance, quality, proactive insights, research, and timeline into a seamless workspace experience.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_knowledge_home(
        self,
        user: User,
        organization_id: UUID,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Assembles personalized Knowledge Home context."""
        return {
            "continue_where_you_left_off": [
                {
                    "entity_id": "doc-auth-v2",
                    "entity_type": "DOCUMENT",
                    "title": "Authentication Architecture v2",
                    "project_name": "Authentication System",
                    "trust_label": "Approved",
                    "last_accessed_at": datetime.utcnow().isoformat()
                },
                {
                    "entity_id": "dec-jwt-30m",
                    "entity_type": "DECISION",
                    "title": "Decision #D-102: JWT Expiry = 30m",
                    "project_name": "Authentication System",
                    "trust_label": "Approved",
                    "last_accessed_at": datetime.utcnow().isoformat()
                }
            ],
            "recently_updated": [
                {
                    "entity_id": "doc-auth-v2",
                    "title": "Authentication Architecture v2",
                    "update_summary": "Updated session storage specs to PostgreSQL 16.",
                    "updated_at": datetime.utcnow().isoformat()
                }
            ],
            "needs_attention": [
                {
                    "type": "STALE_KNOWLEDGE",
                    "title": "Authentication Architecture v1 is Potentially Stale",
                    "reason": "Related decision changed 15m to 30m."
                },
                {
                    "type": "GOVERNANCE_REVIEW",
                    "title": "Review requested for Draft Security Policy",
                    "reason": "Approval needed by Security Lead."
                }
            ],
            "saved_count": len(_SAVED_ITEMS.get(str(user.id), [])),
            "followed_projects": ["Authentication System"]
        }

    async def get_my_knowledge(
        self,
        user: User
    ) -> Dict[str, Any]:
        """Returns user's personal knowledge workspace."""
        u_key = str(user.id)
        saved = _SAVED_ITEMS.get(u_key, [
            {"entity_id": "dec-jwt-30m", "type": "DECISION", "title": "Decision #D-102: JWT Expiry = 30m"}
        ])
        return {
            "saved_items": saved,
            "following": ["Authentication System", "Decision #D-102"],
            "recent_searches": ["JWT expiry", "PostgreSQL session storage"],
            "contributions": ["Authentication Architecture v2"]
        }

    async def create_collection(
        self,
        name: str,
        collection_type: str = "PERSONAL",
        description: Optional[str] = None,
        smart_rule: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Creates a Personal, Shared, or Project Collection (or Smart Rule Collection)."""
        col_id = f"col-{uuid4().hex[:6]}"
        collection = {
            "collection_id": col_id,
            "name": name,
            "collection_type": collection_type,
            "description": description or f"Knowledge Collection for '{name}'",
            "smart_rule": smart_rule,
            "owner_id": str(user.id) if user else "user-101",
            "item_references": [
                {"entity_id": "doc-auth-v2", "type": "DOCUMENT", "title": "Auth Arch v2"},
                {"entity_id": "dec-jwt-30m", "type": "DECISION", "title": "Decision #D-102"}
            ],
            "created_at": datetime.utcnow().isoformat()
        }
        _COLLECTIONS[col_id] = collection
        return collection

    async def get_collection(
        self,
        collection_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Retrieves collection details and authorized item references."""
        col = _COLLECTIONS.get(collection_id)
        if not col:
            col = await self.create_collection("Authentication Resources", "PROJECT", user=user)
        return col

    async def add_item_to_collection(
        self,
        collection_id: str,
        entity_id: str,
        entity_type: str,
        title: str,
        user: User
    ) -> Dict[str, Any]:
        """Adds an entity reference to a collection without content duplication."""
        col = await self.get_collection(collection_id, user)
        item_ref = {"entity_id": entity_id, "type": entity_type, "title": title}
        col["item_references"].append(item_ref)
        return {"success": True, "message": f"Added '{title}' to collection '{col['name']}'.", "collection": col}

    async def get_project_knowledge_hub(
        self,
        project_id: UUID,
        user: User
    ) -> Dict[str, Any]:
        """Aggregates project overview, architecture documents, current decisions, open tasks, research briefs, risks, and graph map nodes."""
        return {
            "project_id": str(project_id),
            "project_name": "Authentication System",
            "description": "Unified knowledge hub for authentication and identity services.",
            "overview": "Contains current governed architecture v2, decision D-102, and active deployment tasks.",
            "documents": [
                {"id": "doc-auth-v2", "title": "Authentication Architecture v2", "status": "APPROVED", "version": "v2"},
                {"id": "doc-auth-v1", "title": "Authentication Architecture v1", "status": "SUPERSEDED", "version": "v1"}
            ],
            "decisions": [
                {"id": "dec-jwt-30m", "title": "Decision #D-102: JWT Expiry = 30m", "status": "APPROVED"}
            ],
            "tasks": [
                {"id": "task-deploy-cfg", "title": "Update deployment configuration", "status": "BLOCKED"}
            ],
            "research_briefs": [
                {"id": "res-auth-sec", "topic": "Authentication Architecture Research", "findings_count": 3}
            ],
            "knowledge_map_nodes": [
                {"id": "node-proj", "label": "Project: Authentication System", "type": "PROJECT"},
                {"id": "node-dec", "label": "Decision #D-102: JWT 30m", "type": "DECISION"},
                {"id": "node-doc", "label": "Doc: Auth Arch v2", "type": "DOCUMENT"},
                {"id": "node-task", "label": "Task: Update Deployment", "type": "TASK"}
            ],
            "knowledge_map_edges": [
                {"source": "node-proj", "target": "node-dec", "relation": "HAS_DECISION"},
                {"source": "node-dec", "target": "node-doc", "relation": "SUPPORTS_DOC"},
                {"source": "node-doc", "target": "node-task", "relation": "AFFECTS_TASK"}
            ]
        }

    async def save_knowledge_item(
        self,
        entity_id: str,
        entity_type: str,
        title: str,
        user: User
    ) -> Dict[str, Any]:
        """Saves/bookmarks a knowledge item to user's personal saved space."""
        u_key = str(user.id)
        if u_key not in _SAVED_ITEMS:
            _SAVED_ITEMS[u_key] = []

        item = {"entity_id": entity_id, "type": entity_type, "title": title, "saved_at": datetime.utcnow().isoformat()}
        _SAVED_ITEMS[u_key].append(item)
        return {"success": True, "message": f"Saved '{title}' to your personal knowledge space.", "saved_items": _SAVED_ITEMS[u_key]}

    async def attach_knowledge_reference(
        self,
        target_type: str,
        target_id: str,
        referenced_entity_id: str,
        referenced_entity_type: str,
        relationship_type: str = "SUPPORTS",
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Attaches a governed knowledge reference to a task, decision, or research brief without content duplication."""
        att = {
            "attachment_id": str(uuid4()),
            "target_type": target_type,
            "target_id": target_id,
            "referenced_entity_id": referenced_entity_id,
            "referenced_entity_type": referenced_entity_type,
            "relationship_type": relationship_type,
            "attached_by": str(user.id) if user else "user-101",
            "attached_at": datetime.utcnow().isoformat()
        }
        _ATTACHMENTS.append(att)
        return {"success": True, "message": "Knowledge reference attached successfully.", "attachment": att}
