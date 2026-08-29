"""
MindMesh — Cognitive Agent Provenance & Revalidation Service (CA-07)

Enforces strict runtime provenance revalidation and source authorization boundaries:
CURRENT USER PERMISSION + OUTPUT ACCESS + SOURCE ACCESS
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.documents.models import Document
from app.projects.models import Project
from app.models.conversations import Conversation
from app.models.message import Message
from app.agents.cognitive_knowledge import CognitiveAgentKnowledgeService

logger = logging.getLogger(__name__)


class CognitiveAgentProvenanceService:
    """
    Service enforcing factual provenance revalidation, staleness detection,
    and source authorization scrubbing for Cognitive Agent Outputs.
    """

    @staticmethod
    async def revalidate_output_provenance(
        db: AsyncSession,
        current_user: User,
        organization_id: UUID,
        workspace_id: Optional[UUID],
        raw_provenance: Optional[List[Dict[str, Any]]],
        output_created_at: datetime
    ) -> List[Dict[str, Any]]:
        """
        Revalidates each provenance source against current user permissions and database state.
        
        Rules:
        1. If source was deleted or user lost access: mask title/content and set is_available=False.
        2. If source was updated after output_created_at: set is_stale=True.
        3. Preserves exact message/document navigation metadata for authorized items.
        """
        if not raw_provenance or not isinstance(raw_provenance, list):
            return []

        if not workspace_id:
            # If no workspace context, mark sources as unavailable for safety
            return [
                {
                    "source_type": item.get("source_type", "unknown"),
                    "source_id": item.get("source_id"),
                    "title": "Source Unavailable",
                    "is_available": False,
                    "status_message": "Source no longer available."
                }
                for item in raw_provenance
            ]

        # Fetch current user authorized items in workspace
        selectable = await CognitiveAgentKnowledgeService.get_user_selectable_knowledge_options(
            db=db,
            current_user=current_user,
            organization_id=organization_id,
            workspace_id=workspace_id
        )

        authorized_proj_map = {p["id"]: p for p in selectable["projects"]}
        authorized_doc_map = {d["id"]: d for d in selectable["documents"]}
        authorized_conv_map = {c["id"]: c for c in selectable["conversations"]}

        revalidated: List[Dict[str, Any]] = []

        for item in raw_provenance:
            if not isinstance(item, dict):
                continue

            src_type = str(item.get("source_type", "")).lower()
            src_id = item.get("source_id")

            if not src_id:
                continue

            clean_item: Dict[str, Any] = {
                "source_type": src_type,
                "source_id": src_id,
                "title": item.get("title", "Untitled Source"),
                "is_available": False,
                "is_stale": False,
                "status_message": None,
                "stale_message": None,
                "retrieved_at": item.get("retrieved_at")
            }

            if src_type == "document":
                if src_id in authorized_doc_map:
                    clean_item["is_available"] = True
                    clean_item["title"] = item.get("title") or authorized_doc_map[src_id].get("title", "Document")
                    clean_item["filename"] = item.get("filename")
                    clean_item["mime_type"] = item.get("mime_type")

                    # Check source staleness against database entity
                    doc_stmt = select(Document).where(Document.id == UUID(src_id), Document.deleted_at.is_(None))
                    doc_obj = (await db.execute(doc_stmt)).scalar_one_or_none()
                    if doc_obj and doc_obj.updated_at and doc_obj.updated_at > output_created_at:
                        clean_item["is_stale"] = True
                        clean_item["stale_message"] = "Source updated since this analysis."
                else:
                    # Check if document exists at all (deleted vs revoked permission)
                    doc_stmt = select(Document.id).where(Document.id == UUID(src_id), Document.deleted_at.is_(None))
                    exists = (await db.execute(doc_stmt)).scalar_one_or_none()
                    clean_item["title"] = "Source Unavailable"
                    clean_item["is_available"] = False
                    clean_item["status_message"] = "Original source is no longer available." if not exists else "Source no longer available (permission revoked)."

            elif src_type == "conversation":
                if src_id in authorized_conv_map:
                    clean_item["is_available"] = True
                    clean_item["title"] = item.get("title") or authorized_conv_map[src_id].get("title", "Conversation")
                    clean_item["conversation_id"] = src_id
                    clean_item["message_id"] = item.get("message_id")
                    clean_item["message_text"] = item.get("message_text")

                    # Validate exact message if message_id is provided
                    if item.get("message_id"):
                        try:
                            msg_uuid = UUID(str(item["message_id"]))
                            msg_stmt = select(Message).where(Message.id == msg_uuid, Message.deleted_at.is_(None))
                            msg_obj = (await db.execute(msg_stmt)).scalar_one_or_none()
                            if not msg_obj:
                                clean_item["message_id"] = None
                                clean_item["status_message"] = "Target message has been deleted."
                        except Exception:
                            clean_item["message_id"] = None
                else:
                    clean_item["title"] = "Source Unavailable"
                    clean_item["is_available"] = False
                    clean_item["status_message"] = "Source no longer available."

            elif src_type == "project":
                if src_id in authorized_proj_map:
                    clean_item["is_available"] = True
                    clean_item["title"] = item.get("title") or authorized_proj_map[src_id].get("name", "Project")
                    clean_item["project_id"] = src_id

                    proj_stmt = select(Project).where(Project.id == UUID(src_id), Project.deleted_at.is_(None))
                    proj_obj = (await db.execute(proj_stmt)).scalar_one_or_none()
                    if proj_obj and proj_obj.updated_at and proj_obj.updated_at > output_created_at:
                        clean_item["is_stale"] = True
                        clean_item["stale_message"] = "Source updated since this analysis."
                else:
                    clean_item["title"] = "Source Unavailable"
                    clean_item["is_available"] = False
                    clean_item["status_message"] = "Source no longer available."

            else:
                # Other existing entities
                clean_item["is_available"] = True
                clean_item["title"] = item.get("title", "Knowledge Source")

            revalidated.append(clean_item)

        return revalidated
