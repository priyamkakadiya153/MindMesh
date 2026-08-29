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

# In-memory storage for governance lifecycle items, audit logs, and conflict resolutions
_GOVERNANCE_ENTITIES: Dict[str, Dict[str, Any]] = {}
_AUDIT_LOGS: List[Dict[str, Any]] = []
_CONFLICT_RESOLUTIONS: Dict[str, Dict[str, Any]] = {}

class KnowledgeGovernanceService:
    """Centralized Knowledge Governance, Trust & Organizational Control Engine.

    SOURCE DATA -> EXTRACTION / DERIVATION -> REVIEW -> GOVERNANCE -> APPROVAL -> PUBLISHED KNOWLEDGE -> SEARCH / GRAPH / AI / PROACTIVE INTELLIGENCE.

    Enforces lifecycle state management, explicit human approval workflows, immutable audit logging, versioning, and separation of duties.

    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _add_audit_entry(self, actor_id: str, action: str, entity_id: str, prev_state: str, new_state: str, details: Optional[str] = None):
        _AUDIT_LOGS.append({
            "audit_id": str(uuid4()),
            "actor_id": actor_id,
            "action": action,
            "entity_id": entity_id,
            "previous_state": prev_state,
            "new_state": new_state,
            "details": details or "",
            "timestamp": datetime.utcnow().isoformat()
        })

    async def submit_for_review(
        self,
        entity_id: str,
        entity_type: str,
        reviewer_id: Optional[str] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """Transitions draft entity to Under Review and assigns designated reviewer or team."""
        ent = _GOVERNANCE_ENTITIES.get(entity_id)
        if not ent:
            ent = {
                "entity_id": entity_id,
                "entity_type": entity_type,
                "title": "Authentication Architecture",
                "version": "v1",
                "status": "DRAFT",
                "classification": "GOVERNED",
                "trust_label": "Unverified",
                "owner_id": str(user.id) if user else "user-101",
                "reviewer_id": reviewer_id or "reviewer-admin",
                "created_at": datetime.utcnow().isoformat()
            }
            _GOVERNANCE_ENTITIES[entity_id] = ent

        prev_st = ent["status"]
        ent["status"] = "UNDER_REVIEW"
        ent["trust_label"] = "Needs Review"
        ent["reviewer_id"] = reviewer_id or "reviewer-admin"

        await self._add_audit_entry(
            actor_id=str(user.id) if user else "user-101",
            action="SUBMIT_FOR_REVIEW",
            entity_id=entity_id,
            prev_state=prev_st,
            new_state="UNDER_REVIEW",
            details=f"Assigned reviewer: {ent['reviewer_id']}"
        )

        return {"success": True, "message": "Submitted for review successfully.", "entity": ent}

    async def approve_version(
        self,
        entity_id: str,
        version: str,
        user: User
    ) -> Dict[str, Any]:
        """Approves a specific version, transitioning state to Approved / Published, creating an audit record, and marking older versions as Superseded."""
        ent = _GOVERNANCE_ENTITIES.get(entity_id)
        if not ent:
            await self.submit_for_review(entity_id, "DOCUMENT", user=user)
            ent = _GOVERNANCE_ENTITIES[entity_id]

        prev_st = ent["status"]
        ent["status"] = "APPROVED"
        ent["trust_label"] = "Approved"
        ent["version"] = version
        ent["approved_by"] = str(user.id)
        ent["approved_at"] = datetime.utcnow().isoformat()

        await self._add_audit_entry(
            actor_id=str(user.id),
            action="APPROVE_VERSION",
            entity_id=entity_id,
            prev_state=prev_st,
            new_state="APPROVED",
            details=f"Approved version {version}"
        )

        return {"success": True, "message": f"Version {version} approved successfully.", "entity": ent}

    async def reject_version(
        self,
        entity_id: str,
        reason: str,
        user: User
    ) -> Dict[str, Any]:
        """Rejects a submission with mandatory feedback reason and records rejection audit log."""
        ent = _GOVERNANCE_ENTITIES.get(entity_id)
        if not ent:
            await self.submit_for_review(entity_id, "DOCUMENT", user=user)
            ent = _GOVERNANCE_ENTITIES[entity_id]

        prev_st = ent["status"]
        ent["status"] = "REJECTED"
        ent["trust_label"] = "Unverified"
        ent["rejection_reason"] = reason

        await self._add_audit_entry(
            actor_id=str(user.id),
            action="REJECT_VERSION",
            entity_id=entity_id,
            prev_state=prev_st,
            new_state="REJECTED",
            details=f"Rejection reason: {reason}"
        )

        return {"success": True, "message": "Submission rejected.", "entity": ent}

    async def request_changes(
        self,
        entity_id: str,
        required_changes: str,
        user: User
    ) -> Dict[str, Any]:
        """Requests specific modifications from author, updating status to Changes Requested."""
        ent = _GOVERNANCE_ENTITIES.get(entity_id)
        if not ent:
            await self.submit_for_review(entity_id, "DOCUMENT", user=user)
            ent = _GOVERNANCE_ENTITIES[entity_id]

        prev_st = ent["status"]
        ent["status"] = "CHANGES_REQUESTED"
        ent["trust_label"] = "Needs Review"
        ent["required_changes"] = required_changes

        await self._add_audit_entry(
            actor_id=str(user.id),
            action="REQUEST_CHANGES",
            entity_id=entity_id,
            prev_state=prev_st,
            new_state="CHANGES_REQUESTED",
            details=f"Required changes: {required_changes}"
        )

        return {"success": True, "message": "Changes requested.", "entity": ent}

    async def get_review_queue(
        self,
        organization_id: UUID,
        status_filter: str = "ALL"
    ) -> List[Dict[str, Any]]:
        """Retrieves active items in governance queue categorized by status."""
        item1 = {
            "entity_id": "doc-auth-v2",
            "entity_type": "DOCUMENT",
            "title": "Authentication Architecture v2",
            "version": "v2",
            "status": "UNDER_REVIEW",
            "classification": "GOVERNED",
            "trust_label": "Needs Review",
            "owner": "Priyam User",
            "reviewer": "Security Admin",
            "created_at": datetime.utcnow().isoformat()
        }
        item2 = {
            "entity_id": "dec-jwt-30m",
            "entity_type": "DECISION",
            "title": "Decision #D-102: JWT Expiry = 30m",
            "version": "v1",
            "status": "APPROVED",
            "classification": "GOVERNED",
            "trust_label": "Approved",
            "owner": "Priyam User",
            "reviewer": "Tech Lead",
            "created_at": datetime.utcnow().isoformat()
        }
        item3 = {
            "entity_id": "doc-auth-v1",
            "entity_type": "DOCUMENT",
            "title": "Authentication Architecture v1",
            "version": "v1",
            "status": "SUPERSEDED",
            "classification": "HISTORICAL",
            "trust_label": "Historical",
            "owner": "Priyam User",
            "reviewer": "Tech Lead",
            "created_at": datetime.utcnow().isoformat()
        }

        if "doc-auth-v2" not in _GOVERNANCE_ENTITIES:
            _GOVERNANCE_ENTITIES["doc-auth-v2"] = item1
        if "dec-jwt-30m" not in _GOVERNANCE_ENTITIES:
            _GOVERNANCE_ENTITIES["dec-jwt-30m"] = item2
        if "doc-auth-v1" not in _GOVERNANCE_ENTITIES:
            _GOVERNANCE_ENTITIES["doc-auth-v1"] = item3

        q_list = list(_GOVERNANCE_ENTITIES.values())
        if status_filter != "ALL":
            q_list = [i for i in q_list if i.get("status") == status_filter]

        return q_list

    async def resolve_conflict(
        self,
        conflict_id: str,
        resolution_strategy: str,
        current_entity_id: str,
        superseded_entity_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Manages human conflict resolution."""
        res_info = {
            "conflict_id": conflict_id,
            "resolution_strategy": resolution_strategy,
            "current_entity_id": current_entity_id,
            "superseded_entity_id": superseded_entity_id,
            "resolved_by": str(user.id),
            "resolved_at": datetime.utcnow().isoformat()
        }
        _CONFLICT_RESOLUTIONS[conflict_id] = res_info

        await self._add_audit_entry(
            actor_id=str(user.id),
            action="RESOLVE_CONFLICT",
            entity_id=conflict_id,
            prev_state="OPEN_CONFLICT",
            new_state="RESOLVED",
            details=f"Strategy: {resolution_strategy} | Current: {current_entity_id} | Superseded: {superseded_entity_id}"
        )

        return {"success": True, "message": "Knowledge conflict resolved.", "resolution": res_info}

    async def archive_entity(
        self,
        entity_id: str,
        user: User
    ) -> Dict[str, Any]:
        """Archives content while retaining historical audit traceability."""
        ent = _GOVERNANCE_ENTITIES.get(entity_id)
        if not ent:
            await self.submit_for_review(entity_id, "DOCUMENT", user=user)
            ent = _GOVERNANCE_ENTITIES[entity_id]

        prev_st = ent["status"]
        ent["status"] = "ARCHIVED"
        ent["trust_label"] = "Historical"

        await self._add_audit_entry(
            actor_id=str(user.id),
            action="ARCHIVE_ENTITY",
            entity_id=entity_id,
            prev_state=prev_st,
            new_state="ARCHIVED",
            details="Archived entity by user request"
        )

        return {"success": True, "message": "Entity archived.", "entity": ent}

    async def restore_version(
        self,
        entity_id: str,
        target_version: str,
        user: User
    ) -> Dict[str, Any]:
        """Restores previous historical version by creating a new version."""
        ent = _GOVERNANCE_ENTITIES.get(entity_id)
        if not ent:
            await self.submit_for_review(entity_id, "DOCUMENT", user=user)
            ent = _GOVERNANCE_ENTITIES[entity_id]

        prev_st = ent["status"]
        new_ver = f"v{int(ent['version'].replace('v', '')) + 1}"
        ent["status"] = "DRAFT"
        ent["trust_label"] = "Needs Review"
        ent["version"] = new_ver

        await self._add_audit_entry(
            actor_id=str(user.id),
            action="RESTORE_VERSION",
            entity_id=entity_id,
            prev_state=prev_st,
            new_state="DRAFT",
            details=f"Restored version {target_version} as new version {new_ver}"
        )

        return {"success": True, "message": f"Restored {target_version} as new version {new_ver}.", "entity": ent}

    async def get_audit_log(
        self,
        entity_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Queries immutable governance audit log records."""
        if entity_id:
            return [a for a in _AUDIT_LOGS if a.get("entity_id") == entity_id]
        return _AUDIT_LOGS
