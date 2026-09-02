from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
import bcrypt
from .config import settings

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password or not plain_password:
        return False
    try:
        pwd_bytes = plain_password.encode("utf-8")[:72]
        hash_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes, hash_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = (password or "").encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")



import uuid

def create_access_token(
    subject: Union[str, Any] = None,
    org_id: Optional[Union[str, Any]] = None,
    workspace_id: Optional[Union[str, Any]] = None,
    role: Optional[str] = None,
    session_id: Optional[Union[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
    data: Optional[dict] = None
) -> str:
    if data is None:
        data = {}
    if subject is not None:
        data["sub"] = str(subject)
    if org_id is not None:
        data["org_id"] = str(org_id)
    if workspace_id is not None:
        data["workspace_id"] = str(workspace_id)
    if role is not None:
        data["role"] = str(role)
    if session_id is not None:
        data["session_id"] = str(session_id)
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
        
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "version": 1,
        **data
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm="HS256")
    return encoded_jwt

def create_refresh_token(
    subject: Union[str, Any] = None,
    org_id: Optional[Union[str, Any]] = None,
    workspace_id: Optional[Union[str, Any]] = None,
    role: Optional[str] = None,
    session_id: Optional[Union[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
    data: Optional[dict] = None
) -> str:
    if data is None:
        data = {}
    if subject is not None:
        data["sub"] = str(subject)
    if org_id is not None:
        data["org_id"] = str(org_id)
    if workspace_id is not None:
        data["workspace_id"] = str(workspace_id)
    if role is not None:
        data["role"] = str(role)
    if session_id is not None:
        data["session_id"] = str(session_id)

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=30)
        
    to_encode = {
        "exp": expire,
        "iat": datetime.utcnow(),
        "version": 1,
        **data
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET, algorithm="HS256")
    return encoded_jwt

def decode_token_payload(token: str, secret: Optional[str] = None) -> Optional[dict]:
    if secret is None:
        secret = settings.JWT_SECRET
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except Exception:
        return None

def decode_token(token: str, secret: Optional[str] = None) -> Optional[str]:
    payload = decode_token_payload(token, secret)
    return payload.get("sub") if payload else None



