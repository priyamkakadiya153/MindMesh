from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db_session
from ..core.security import decode_token
from ..core.config import settings
from ..models.user import User
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    db: AsyncSession = Depends(get_db_session),
    token: str = Depends(oauth2_scheme)
) -> User:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session has expired. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    from ..core.security import decode_token_payload
    payload = decode_token_payload(token, settings.JWT_SECRET)
    if payload is None:
        raise credentials_exception
    
    user_id_str = payload.get("sub")
    session_id_str = payload.get("session_id")
    if not user_id_str or not session_id_str:
        raise credentials_exception
        
    try:
        user_id = UUID(user_id_str)
        session_id = UUID(session_id_str)
    except ValueError:
        raise credentials_exception
        
    from ..models.session import UserSession
    from datetime import datetime
    
    # Verify session is valid in DB
    session_stmt = select(UserSession).where(
        UserSession.id == session_id,
        UserSession.revoked == False,
        UserSession.expires_at > datetime.utcnow()
    )
    session_res = await db.execute(session_stmt)
    db_session = session_res.scalar_one_or_none()
    if db_session is None:
        raise credentials_exception
        
    stmt = select(User).where(User.id == user_id, User.is_active == True, User.deleted_at == None)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_from_header_or_query(
    request: Request,
    db: AsyncSession = Depends(get_db_session)
) -> User:
    raw_token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header.split(" ")[1]
    else:
        raw_token = request.query_params.get("token")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Your session has expired or token missing. Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not raw_token:
        raise credentials_exception

    from ..core.security import decode_token_payload
    payload = decode_token_payload(raw_token, settings.JWT_SECRET)
    if payload is None:
        raise credentials_exception

    user_id_str = payload.get("sub")
    session_id_str = payload.get("session_id")
    if not user_id_str or not session_id_str:
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
        session_id = UUID(session_id_str)
    except ValueError:
        raise credentials_exception

    from ..models.session import UserSession
    from datetime import datetime

    session_stmt = select(UserSession).where(
        UserSession.id == session_id,
        UserSession.revoked == False,
        UserSession.expires_at > datetime.utcnow()
    )
    session_res = await db.execute(session_stmt)
    db_session = session_res.scalar_one_or_none()
    if db_session is None:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id, User.is_active == True, User.deleted_at == None)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user



