import logging
from typing import List, Dict, Any, Set
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.documents.models import Document
from app.workspace.models import WorkspaceMember
from app.projects.models import ProjectMember

logger = logging.getLogger(__name__)

class ContextSecurityValidator:
    @staticmethod
    async def validate_context_permissions(
        db: AsyncSession,
        user_id: UUID,
        org_id: UUID,
        document_ids: Set[UUID]
    ) -> bool:
        """Validates that a user has read permission for a set of document IDs.
        
        Enforces:
        - Organization isolation (document organization must match active org).
        - Workspace membership (user must belong to the workspace of the document).
        - Project membership (user must belong to the project if private).
        """
        if not document_ids:
            return True
            
        try:
            # 1. Fetch documents
            stmt = select(Document).where(Document.id.in_(document_ids))
            res = await db.execute(stmt)
            docs = res.scalars().all()
            
            valid_doc_ids = set(doc.id for doc in docs)
            if not valid_doc_ids:
                return True
                
            # Group by workspace and project
            workspaces_to_check = set()
            projects_to_check = set()
            
            for doc in docs:
                # Organization Check
                if doc.organization_id != org_id:
                    logger.warning(f"Tenant violation: Doc {doc.id} org {doc.organization_id} != active {org_id}")
                    return False
                
                workspaces_to_check.add(doc.workspace_id)
                projects_to_check.add(doc.project_id)
                
            # 2. Check workspace membership
            ws_stmt = select(WorkspaceMember.workspace_id).where(
                WorkspaceMember.workspace_id.in_(workspaces_to_check),
                WorkspaceMember.user_id == user_id,
                WorkspaceMember.is_active == True
            )
            ws_res = await db.execute(ws_stmt)
            user_workspaces = set(ws_res.scalars().all())
            
            if not workspaces_to_check.issubset(user_workspaces):
                missing_ws = workspaces_to_check - user_workspaces
                logger.warning(f"Access denied: User {user_id} lacks access to workspaces: {missing_ws}")
                return False
                
            # 3. Check project membership (if project is private or restrict members)
            # Fetch private projects only to verify
            from app.projects.models import Project
            proj_stmt = select(Project).where(
                Project.id.in_(projects_to_check),
                Project.visibility == "private"
            )
            proj_res = await db.execute(proj_stmt)
            private_projects = set(p.id for p in proj_res.scalars().all())
            
            if private_projects:
                pm_stmt = select(ProjectMember.project_id).where(
                    ProjectMember.project_id.in_(private_projects),
                    ProjectMember.user_id == user_id,
                    ProjectMember.is_active == True
                )
                pm_res = await db.execute(pm_stmt)
                user_projects = set(pm_res.scalars().all())
                
                if not private_projects.issubset(user_projects):
                    missing_p = private_projects - user_projects
                    logger.warning(f"Access denied: User {user_id} lacks access to private projects: {missing_p}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating context permissions: {str(e)}", exc_info=True)
            return False
