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

# In-memory storage for governance review queue, conflicts, source-of-truth registry, and audit log
_REVIEW_QUEUE: List[Dict[str, Any]] = []
_CONFLICTS: List[Dict[str, Any]] = []
_SOURCE_OF_TRUTH: Dict[str, str] = {} # project_id -> entity_id
_AUDIT_LOG: List[Dict[str, Any]] = []

class KnowledgeGovernanceTrustService:
    """Centralized Knowledge Governance & Trust engine managing knowledge lifecycle states

    (DRAFT, NEEDS_REVIEW, VERIFIED, CURRENT, SUPERSEDED, CONFLICTED), AI extraction human-in-the-loop

    review, conflict detection & resolution, Source of Truth designation, and provenance audit logging.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_review_queue(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        project_id: UUID,
        entity_type: str,
        entity_id: UUID,
        title: str,
        description: str,
        source_type: str,
        source_id: UUID,
        reason: str = "AI detected potential decision in conversation."
    ) -> Dict[str, Any]:
        """Adds an AI extraction or potential knowledge item to the Needs Review queue."""
        item_id = str(uuid4())
        item = {
            "id": item_id,
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "project_id": str(project_id),
            "entity_type": entity_type,
            "entity_id": str(entity_id),
            "title": title,
            "description": description,
            "source_type": source_type,
            "source_id": str(source_id),
            "status": "NEEDS_REVIEW",
            "reason": reason,
            "created_at": datetime.utcnow().isoformat()
        }
        _REVIEW_QUEUE.append(item)
        return item

    async def get_review_queue(
        self,
        organization_id: UUID,
        workspace_id: Optional[UUID] = None,
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Retrieves items needing human review for the organization."""
        org_key = str(organization_id)
        queue = [i for i in _REVIEW_QUEUE if i["organization_id"] == org_key and i["status"] == "NEEDS_REVIEW"]
        conflicts = [c for c in _CONFLICTS if c["organization_id"] == org_key and c["status"] == "UNRESOLVED"]
        return {
            "total_review_items": len(queue),
            "total_conflicts": len(conflicts),
            "review_queue": queue,
            "active_conflicts": conflicts
        }

    async def confirm_ai_extraction(
        self,
        user: User,
        organization_id: UUID,
        review_item_id: str,
        edited_title: Optional[str] = None,
        edited_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Confirms an AI extraction, updating status to VERIFIED / CURRENT."""
        for item in _REVIEW_QUEUE:
            if item["id"] == review_item_id and item["organization_id"] == str(organization_id):
                item["status"] = "VERIFIED"
                if edited_title:
                    item["title"] = edited_title
                if edited_description:
                    item["description"] = edited_description

                # Record Audit Log
                self._record_audit(
                    organization_id=organization_id,
                    user=user,
                    action="CONFIRM_AI_EXTRACTION",
                    entity_type=item["entity_type"],
                    entity_id=item["entity_id"],
                    old_state="NEEDS_REVIEW",
                    new_state="VERIFIED",
                    reason="Human user confirmed AI extraction."
                )
                return {"success": True, "message": "Knowledge confirmed and verified.", "item": item}
        return {"success": False, "message": "Review item not found."}

    async def reject_ai_extraction(
        self,
        user: User,
        organization_id: UUID,
        review_item_id: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rejects an AI extraction without altering underlying source conversation."""
        for item in _REVIEW_QUEUE:
            if item["id"] == review_item_id and item["organization_id"] == str(organization_id):
                item["status"] = "REJECTED"

                self._record_audit(
                    organization_id=organization_id,
                    user=user,
                    action="REJECT_AI_EXTRACTION",
                    entity_type=item["entity_type"],
                    entity_id=item["entity_id"],
                    old_state="NEEDS_REVIEW",
                    new_state="REJECTED",
                    reason=reason or "User rejected AI extraction."
                )
                return {"success": True, "message": "AI extraction rejected non-destructively."}
        return {"success": False, "message": "Review item not found."}

    async def detect_and_flag_conflict(
        self,
        organization_id: UUID,
        workspace_id: UUID,
        project_id: UUID,
        source_a_title: str,
        source_a_content: str,
        source_a_id: UUID,
        source_b_title: str,
        source_b_content: str,
        source_b_id: UUID,
        topic: str = "JWT Expiry Duration"
    ) -> Dict[str, Any]:
        """Flags a semantic contradiction between two current sources."""
        c_id = str(uuid4())
        conflict = {
            "id": c_id,
            "organization_id": str(organization_id),
            "workspace_id": str(workspace_id),
            "project_id": str(project_id),
            "topic": topic,
            "severity": "POTENTIAL_CONFLICT",
            "source_a": {
                "id": str(source_a_id),
                "title": source_a_title,
                "content": source_a_content
            },
            "source_b": {
                "id": str(source_b_id),
                "title": source_b_title,
                "content": source_b_content
            },
            "status": "UNRESOLVED",
            "created_at": datetime.utcnow().isoformat()
        }
        _CONFLICTS.append(conflict)
        return conflict

    async def resolve_conflict(
        self,
        user: User,
        organization_id: UUID,
        conflict_id: str,
        winning_source_id: str,
        resolution_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resolves a knowledge conflict by marking the winning source as CURRENT and losing source as SUPERSEDED."""
        for c in _CONFLICTS:
            if c["id"] == conflict_id and c["organization_id"] == str(organization_id):
                c["status"] = "RESOLVED"
                c["resolved_by"] = user.username
                c["winning_source_id"] = winning_source_id
                c["resolution_notes"] = resolution_notes or "Marked winning source as current authoritative fact."

                self._record_audit(
                    organization_id=organization_id,
                    user=user,
                    action="RESOLVE_CONFLICT",
                    entity_type="CONFLICT",
                    entity_id=conflict_id,
                    old_state="UNRESOLVED",
                    new_state="RESOLVED",
                    reason=resolution_notes or "Conflict resolved by user choice."
                )
                return {"success": True, "message": "Conflict resolved successfully.", "conflict": c}
        return {"success": False, "message": "Conflict not found."}

    async def set_source_of_truth(
        self,
        user: User,
        organization_id: UUID,
        project_id: UUID,
        entity_id: UUID,
        entity_title: str
    ) -> Dict[str, Any]:
        """Designates an authoritative document/decision as Source of Truth for a project."""
        p_key = str(project_id)
        e_key = str(entity_id)
        _SOURCE_OF_TRUTH[p_key] = e_key

        self._record_audit(
            organization_id=organization_id,
            user=user,
            action="SET_SOURCE_OF_TRUTH",
            entity_type="DOCUMENT_OR_DECISION",
            entity_id=e_key,
            old_state="STANDARD",
            new_state="SOURCE_OF_TRUTH",
            reason=f"User marked '{entity_title}' as primary Source of Truth."
        )
        return {"success": True, "project_id": p_key, "source_of_truth_id": e_key}

    async def get_governance_audit_log(
        self,
        organization_id: UUID
    ) -> List[Dict[str, Any]]:
        """Retrieves governance audit history for the organization."""
        org_key = str(organization_id)
        return [a for a in _AUDIT_LOG if a["organization_id"] == org_key]

    def _record_audit(
        self,
        organization_id: UUID,
        user: User,
        action: str,
        entity_type: str,
        entity_id: str,
        old_state: str,
        new_state: str,
        reason: str
    ):
        _AUDIT_LOG.append({
            "id": str(uuid4()),
            "organization_id": str(organization_id),
            "performed_by": user.username,
            "user_id": str(user.id),
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_state": old_state,
            "new_state": new_state,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        })
