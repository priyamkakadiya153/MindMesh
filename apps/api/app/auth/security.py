import re
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=10, deprecated="auto")

def _truncate_password(password: str) -> str:
    if not password:
        return ""
    # Bcrypt maximum length is 72 UTF-8 bytes
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")

def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate_password(password))

get_password_hash = hash_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        return pwd_context.verify(_truncate_password(plain_password), hashed_password)
    except Exception:
        return False


def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[0-9]", password):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character")
    return True
