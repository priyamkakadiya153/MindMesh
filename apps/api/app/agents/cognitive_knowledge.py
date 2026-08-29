import logging
from typing import List, Dict, Any, Optional, Set
from uuid import UUID
from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember
from app.workspace.models import Workspace, WorkspaceMember
from app.projects.models import Project, ProjectMember
from app.documents.models import Document, DocumentShare
from app.models.conversations import Conversation, ConversationMember
from app.models.cognitive_agent import CognitiveAgent
from app.agents.cognitive_contracts import CognitiveAgentScopeContract, CognitiveAgentScopeType

logger = logging.getLogger(__name__)


class CognitiveAgentKnowledgeService:
    """
    Service enforcing backend Knowledge Scope resolution and authorization boundaries
    for Cognitive Agents in MindMesh (CA-04).
    
    Accessible Knowledge = (User Authorized Knowledge ∩ Agent Configured Scope ∩ Workspace/Org Context)
    """

    @staticmethod
    async def get_user_selectable_knowledge_options(
        db: AsyncSession,
        current_user: User,
        organization_id: UUID,
        workspace_id: UUID
    ) -> Dict[str, Any]:
        """
        Returns all projects, documents, and conversations in the given workspace
        that the current authenticated user is authorized to access.
        """
        # 1. Verify User Workspace Membership
        ws_member_stmt = select(WorkspaceMember.id).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == current_user.id,
            WorkspaceMember.deleted_at.is_(None)
        )
        is_ws_member = (await db.execute(ws_member_stmt)).scalar_one_or_none()
        if not is_ws_member:
            return {"projects": [], "documents": [], "conversations": []}

        # 2. Fetch Authorized Projects
        proj_stmt = select(Project).where(
            Project.organization_id == organization_id,
            Project.workspace_id == workspace_id,
            Project.is_archived == False,
            Project.deleted_at.is_(None),
            or_(
                Project.visibility == "public",
                Project.owner_id == current_user.id,
                Project.id.in_(
                    select(ProjectMember.project_id).where(
                        ProjectMember.user_id == current_user.id,
                        ProjectMember.deleted_at.is_(None)
                    )
                )
            )
        )
        proj_res = await db.execute(proj_stmt)
        projects = proj_res.scalars().all()

        # 3. Fetch Authorized Documents
        doc_stmt = select(Document).where(
            Document.organization_id == organization_id,
            Document.workspace_id == workspace_id,
            Document.deleted_at.is_(None),
            or_(
                Document.visibility == "public",
                Document.uploaded_by == current_user.id,
                Document.id.in_(
                    select(DocumentShare.document_id).where(
                        DocumentShare.shared_with_user_id == current_user.id
                    )
                )
            )
        )
        doc_res = await db.execute(doc_stmt)
        documents = doc_res.scalars().all()

        # 4. Fetch Authorized Conversations
        conv_stmt = select(Conversation).where(
            Conversation.organization_id == organization_id,
            Conversation.workspace_id == workspace_id,
            Conversation.deleted_at.is_(None),
            or_(
                Conversation.participant_one == current_user.id,
                Conversation.participant_two == current_user.id,
                Conversation.id.in_(
                    select(ConversationMember.conversation_id).where(
                        ConversationMember.user_id == current_user.id,
                        ConversationMember.deleted_at.is_(None)
                    )
                )
            )
        )
        conv_res = await db.execute(conv_stmt)
        conversations = conv_res.scalars().all()

        return {
            "projects": [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "description": p.description,
                    "status": p.status
                }
                for p in projects
            ],
            "documents": [
                {
                    "id": str(d.id),
                    "title": d.title or d.filename,
                    "filename": d.filename,
                    "mime_type": d.mime_type,
                    "size": d.size,
                    "project_id": str(d.project_id) if d.project_id else None
                }
                for d in documents
            ],
            "conversations": [
                {
                    "id": str(c.id),
                    "title": c.name or f"Conversation ({str(c.id)[:8]})",
                    "conversation_type": getattr(c, "type", "private"),
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "last_message_id": str(c.last_message_id) if getattr(c, "last_message_id", None) else None,
                    "last_message_text": getattr(c, "last_message_text", None)
                }
                for c in conversations
            ]
        }

    @staticmethod
    async def validate_and_normalize_scope(
        db: AsyncSession,
        scope_data: Dict[str, Any],
        current_user: User,
        organization_id: UUID,
        workspace_id: UUID
    ) -> Dict[str, Any]:
        """
        Validates scope inputs against database authorization boundaries.
        Strips unauthorized or non-existent resource references.
        """
        scope_type = scope_data.get("scope_type", "WORKSPACE")
        
        # Verify scope_type is valid
        try:
            enum_type = CognitiveAgentScopeType(scope_type)
        except ValueError:
            scope_type = CognitiveAgentScopeType.WORKSPACE.value

        selectable = await CognitiveAgentKnowledgeService.get_user_selectable_knowledge_options(
            db, current_user, organization_id, workspace_id
        )

        valid_proj_ids: Set[str] = {p["id"] for p in selectable["projects"]}
        valid_doc_ids: Set[str] = {d["id"] for d in selectable["documents"]}
        valid_conv_ids: Set[str] = {c["id"] for c in selectable["conversations"]}

        # Normalize and filter
        project_id = scope_data.get("project_id")
        if project_id and project_id not in valid_proj_ids:
            project_id = None

        doc_ids = [d for d in scope_data.get("document_ids", []) if d in valid_doc_ids]
        conv_ids = [c for c in scope_data.get("conversation_ids", []) if c in valid_conv_ids]
        channel_ids = scope_data.get("channel_ids", [])

        normalized = {
            "scope_type": scope_type,
            "workspace_id": str(workspace_id),
            "project_id": project_id,
            "document_ids": doc_ids,
            "conversation_ids": conv_ids,
            "channel_ids": channel_ids,
            "restricted_knowledge_keys": scope_data.get("restricted_knowledge_keys", [])
        }

        return normalized

    @staticmethod
    async def resolve_agent_knowledge_boundary(
        db: AsyncSession,
        agent: CognitiveAgent,
        current_user: User,
        organization_id: UUID,
        workspace_id: UUID
    ) -> Dict[str, Any]:
        """
        Resolves the exact allowed knowledge items (documents, projects, conversations)
        the agent is allowed to access.
        
        Enforces the CRITICAL EMPTY SCOPE RULE:
        If an agent has no knowledge scope configured, returns 0 allowed items.
        """
        raw_scope = agent.knowledge_scope
        if not raw_scope or not isinstance(raw_scope, dict):
            return {
                "scope_type": "NONE",
                "accessible_projects": [],
                "accessible_documents": [],
                "accessible_conversations": [],
                "message": "Agent has no knowledge access configured."
            }

        scope_type = raw_scope.get("scope_type", "NONE")

        # Get all resources user is authorized to view in workspace
        selectable = await CognitiveAgentKnowledgeService.get_user_selectable_knowledge_options(
            db, current_user, organization_id, workspace_id
        )

        all_user_projects = selectable["projects"]
        all_user_docs = selectable["documents"]
        all_user_convs = selectable["conversations"]

        if scope_type == CognitiveAgentScopeType.WORKSPACE.value:
            return {
                "scope_type": scope_type,
                "accessible_projects": all_user_projects,
                "accessible_documents": all_user_docs,
                "accessible_conversations": all_user_convs,
                "message": "Agent can access authorized knowledge across this workspace."
            }

        elif scope_type == CognitiveAgentScopeType.PROJECT.value:
            target_proj_id = raw_scope.get("project_id")
            allowed_projects = [p for p in all_user_projects if p["id"] == target_proj_id]
            allowed_docs = [d for d in all_user_docs if d.get("project_id") == target_proj_id]
            
            return {
                "scope_type": scope_type,
                "accessible_projects": allowed_projects,
                "accessible_documents": allowed_docs,
                "accessible_conversations": [],
                "message": f"Agent is scoped to project ID {target_proj_id}." if target_proj_id else "No project configured."
            }

        elif scope_type == CognitiveAgentScopeType.DOCUMENT.value:
            target_doc_ids = set(raw_scope.get("document_ids", []))
            allowed_docs = [d for d in all_user_docs if d["id"] in target_doc_ids]

            return {
                "scope_type": scope_type,
                "accessible_projects": [],
                "accessible_documents": allowed_docs,
                "accessible_conversations": [],
                "message": f"Agent is scoped to {len(allowed_docs)} specific documents."
            }

        elif scope_type == CognitiveAgentScopeType.CONVERSATION.value:
            target_conv_ids = set(raw_scope.get("conversation_ids", []))
            allowed_convs = [c for c in all_user_convs if c["id"] in target_conv_ids]

            return {
                "scope_type": scope_type,
                "accessible_projects": [],
                "accessible_documents": [],
                "accessible_conversations": allowed_convs,
                "message": f"Agent is scoped to {len(allowed_convs)} specific conversations."
            }

        elif scope_type == CognitiveAgentScopeType.SELECTED_KNOWLEDGE.value:
            target_proj_id = raw_scope.get("project_id")
            target_doc_ids = set(raw_scope.get("document_ids", []))
            target_conv_ids = set(raw_scope.get("conversation_ids", []))

            allowed_projects = [p for p in all_user_projects if p["id"] == target_proj_id] if target_proj_id else []
            allowed_docs = [d for d in all_user_docs if d["id"] in target_doc_ids]
            allowed_convs = [c for c in all_user_convs if c["id"] in target_conv_ids]

            return {
                "scope_type": scope_type,
                "accessible_projects": allowed_projects,
                "accessible_documents": allowed_docs,
                "accessible_conversations": allowed_convs,
                "message": f"Agent is scoped to selected knowledge ({len(allowed_projects)} projects, {len(allowed_docs)} documents, {len(allowed_convs)} conversations)."
            }

        else:
            return {
                "scope_type": "NONE",
                "accessible_projects": [],
                "accessible_documents": [],
                "accessible_conversations": [],
                "message": "Agent has no valid knowledge access configured."
            }
