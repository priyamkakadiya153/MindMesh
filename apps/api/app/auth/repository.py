from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User
from ..models.session import UserSession
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from .utils import normalize_phone_number

class AuthRepository:
    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        stmt = select(User).where(User.email == email, User.deleted_at == None)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_user_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        stmt = select(User).where(User.username == username, User.deleted_at == None)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_user_by_firebase_uid(self, db: AsyncSession, firebase_uid: str) -> Optional[User]:
        stmt = select(User).where(User.firebase_uid == firebase_uid, User.deleted_at == None).order_by(User.created_at.desc())
        res = await db.execute(stmt)
        return res.scalars().first()

    async def get_user_by_phone_number(self, db: AsyncSession, phone_number: str) -> Optional[User]:
        normalized = normalize_phone_number(phone_number)
        if not normalized:
            return None
            
        stmt = select(User).where(User.phone_number == normalized, User.deleted_at == None).order_by(User.created_at.desc())
        res = await db.execute(stmt)
        user = res.scalars().first()
        if user:
            return user

        # Fallback comparison against unnormalized phone numbers stored previously
        all_stmt = select(User).where(User.phone_number.isnot(None), User.deleted_at == None)
        all_res = await db.execute(all_stmt)
        all_users = all_res.scalars().all()
        for u in all_users:
            if u.phone_number and normalize_phone_number(u.phone_number) == normalized:
                return u
        return None

    async def create_user(self, db: AsyncSession, user_obj: User) -> User:
        db.add(user_obj)
        await db.flush()
        return user_obj

    async def save_session(self, db: AsyncSession, session_obj: UserSession) -> UserSession:
        db.add(session_obj)
        await db.flush()
        return session_obj

    async def get_session_by_hash(self, db: AsyncSession, refresh_token_hash: str) -> Optional[UserSession]:
        stmt = select(UserSession).where(
            UserSession.refresh_token_hash == refresh_token_hash,
            UserSession.revoked == False,
            UserSession.expires_at > datetime.utcnow()
        )
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_session_by_id(self, db: AsyncSession, session_id: UUID) -> Optional[UserSession]:
        stmt = select(UserSession).where(UserSession.id == session_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_active_sessions(self, db: AsyncSession, user_id: UUID) -> List[UserSession]:
        stmt = select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,
            UserSession.expires_at > datetime.utcnow()
        ).order_by(UserSession.created_at.desc())
        res = await db.execute(stmt)
        return list(res.scalars().all())
