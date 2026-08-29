from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.security import decode_token
from ..core.database import AsyncSessionLocal
from ..organizations.repository import OrganizationRepository
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from ..models.organization_member import OrganizationMember
from ..models.role import Role
from uuid import UUID

org_repo = OrganizationRepository()

class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if request.method == "OPTIONS":
            return await call_next(request)
            
        if (not path.startswith("/api/v1/") or 
            path.startswith("/api/v1/auth/") or 
            path.startswith("/api/v1/monitoring/")):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        token = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            token = request.cookies.get("access_token")

        if not token:
            return Response(
                '{"detail": "Your session has expired. Please sign in again."}',
                status_code=401,
                media_type="application/json"
            )
        
        from ..core.security import decode_token_payload
        from ..models.session import UserSession
        from datetime import datetime

        payload = decode_token_payload(token)
        if not payload:
            return Response(
                '{"detail": "Your session has expired. Please sign in again."}',
                status_code=401,
                media_type="application/json"
            )
            
        payload_sub = payload.get("sub")
        session_id_str = payload.get("session_id")
        if not payload_sub or not session_id_str:
            return Response(
                '{"detail": "Your session has expired. Please sign in again."}',
                status_code=401,
                media_type="application/json"
            )
            
        try:
            user_id = UUID(payload_sub)
            session_id = UUID(session_id_str)
        except Exception:
            return Response(
                '{"detail": "Your session has expired. Please sign in again."}',
                status_code=401,
                media_type="application/json"
            )

        org_id_header = request.headers.get("X-Organization-ID")
        org_id_query = request.query_params.get("organization_id")
        
        active_org_id = None
        if org_id_header and org_id_header.strip() and org_id_header.strip().lower() not in ("null", "undefined"):
            try:
                active_org_id = UUID(org_id_header.strip())
            except ValueError:
                active_org_id = None
        elif org_id_query and org_id_query.strip() and org_id_query.strip().lower() not in ("null", "undefined"):
            try:
                active_org_id = UUID(org_id_query.strip())
            except ValueError:
                active_org_id = None

        from ..core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            # Verify session is valid in DB
            session_stmt = select(UserSession).where(
                UserSession.id == session_id,
                UserSession.revoked == False,
                UserSession.expires_at > datetime.utcnow()
            )
            session_res = await db.execute(session_stmt)
            db_session = session_res.scalar_one_or_none()
            if db_session is None:
                return Response(
                    '{"detail": "Your session has expired. Please sign in again."}',
                    status_code=401,
                    media_type="application/json"
                )

            # Store session_id in request state for endpoints to access
            request.state.session_id = session_id

            from ..models.user import User
            user_stmt = select(User).where(User.id == user_id, User.is_active == True, User.deleted_at == None)
            user_res = await db.execute(user_stmt)
            user = user_res.scalar_one_or_none()
            if not user:
                return Response(
                    '{"detail": "User account inactive or not found."}',
                    status_code=401,
                    media_type="application/json"
                )

            if not active_org_id:
                if user.current_organization_id:
                    # check if they have membership in their current_organization_id
                    mem_check_stmt = select(OrganizationMember).where(
                        OrganizationMember.organization_id == user.current_organization_id,
                        OrganizationMember.user_id == user_id,
                        OrganizationMember.deleted_at == None
                    )
                    mem_check_res = await db.execute(mem_check_stmt)
                    if mem_check_res.scalar_one_or_none():
                        active_org_id = user.current_organization_id

                if not active_org_id:
                    memberships = await org_repo.list_user_organizations(db, user_id)
                    if not memberships:
                        return Response("Forbidden: User has no active organization membership", status_code=403)
                    active_org_id = memberships[0].organization_id

            stmt = (
                select(OrganizationMember)
                .options(selectinload(OrganizationMember.role_rel).selectinload(Role.permissions))
                .where(
                    OrganizationMember.organization_id == active_org_id,
                    OrganizationMember.user_id == user_id,
                    OrganizationMember.deleted_at == None
                )
            )
            res = await db.execute(stmt)
            membership = res.scalar_one_or_none()
            if not membership:
                return Response("Forbidden: Not a member of the resolved organization", status_code=403)

            request.state.user_id = user_id
            request.state.org_id = active_org_id
            request.state.authenticated_user = user
            request.state.role = membership.role if isinstance(membership.role, str) else (membership.role_rel.name if membership.role_rel else "member")
            request.state.permissions = [p.name for p in membership.role_rel.permissions] if (membership.role_rel and membership.role_rel.permissions) else []


        response = await call_next(request)
        return response
