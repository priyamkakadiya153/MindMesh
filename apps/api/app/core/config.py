from pathlib import Path
from typing import Optional, Any
from urllib.parse import quote_plus, unquote
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
ROOT_ENV = BASE_DIR / ".env"
API_ENV = Path(__file__).resolve().parent.parent.parent / ".env"
LOCAL_ENV = Path(".env").resolve()

existing_env_files = []
for p in [ROOT_ENV, API_ENV, LOCAL_ENV]:
    if p.exists() and str(p) not in existing_env_files:
        existing_env_files.append(str(p))

if not existing_env_files:
    existing_env_files = [".env"]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=existing_env_files,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    PORT: int = 4000
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mindmesh"
    REDIS_URL: str = "redis://localhost:6379"
    JWT_SECRET: str = "mindmesh_super_secret_jwt_key_123!"
    JWT_REFRESH_SECRET: str = "mindmesh_refresh_token_secret_key_456!"
    NODE_ENV: str = "development"
    GEMINI_API_KEY: Optional[str] = None

    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_PROJECT_ID: Optional[str] = None

    # SMTP Configuration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: str = "MindMesh"
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True

    # Documents & Storage configurations
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "txt", "md", "xlsx", "csv", "pptx", "png", "jpg", "jpeg"]
    STORAGE_PROVIDER: str = "local"
    UPLOAD_DIRECTORY: str = "uploads"
    TEMP_DIRECTORY: str = "temp"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Any) -> str:
        if not v:
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/mindmesh"
        s = str(v).strip().strip('\'"\\').strip()
        if s.startswith("postgres://"):
            s = "postgresql+asyncpg://" + s[len("postgres://"):]
        elif s.startswith("postgresql://"):
            s = "postgresql+asyncpg://" + s[len("postgresql://"):]
        elif not s.startswith("postgresql+asyncpg://") and "://" in s:
            _, rest = s.split("://", 1)
            s = f"postgresql+asyncpg://{rest}"
        elif "://" not in s:
            print(f"[CONFIG WARNING] Invalid DATABASE_URL scheme '{s}', defaulting to localhost asyncpg.")
            return "postgresql+asyncpg://postgres:postgres@localhost:5432/mindmesh"

        # Safely URL-encode password in case of special characters (@, #, ?, %, [, ], etc.)
        scheme, remainder = s.split("://", 1)
        if "@" in remainder:
            cred_part, host_part = remainder.rsplit("@", 1)
            if ":" in cred_part:
                user, pwd = cred_part.split(":", 1)
                encoded_pwd = quote_plus(unquote(pwd))
                s = f"{scheme}://{user}:{encoded_pwd}@{host_part}"
        return s

    @field_validator("REDIS_URL", "JWT_SECRET", "JWT_REFRESH_SECRET", "GEMINI_API_KEY", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL", mode="before")
    @classmethod
    def clean_string_settings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().strip('\'"\\').strip()
        return v

    def validate_startup_config(self) -> None:
        """Verifies required settings at startup and logs loaded configuration with passwords masked."""
        host_ok = bool(self.SMTP_HOST)
        port_ok = bool(self.SMTP_PORT)
        user_ok = bool(self.SMTP_USERNAME and self.SMTP_USERNAME.strip())
        pass_ok = bool(self.SMTP_PASSWORD and self.SMTP_PASSWORD.strip())
        from_ok = bool(self.SMTP_FROM_EMAIL and self.SMTP_FROM_EMAIL.strip())

        # Mask database URL for clean logging
        masked_db = self.DATABASE_URL
        if "@" in masked_db:
            scheme_user, host_db = masked_db.rsplit("@", 1)
            if ":" in scheme_user:
                scheme_u, _ = scheme_user.rsplit(":", 1)
                masked_db = f"{scheme_u}:***@{host_db}"

        # Mask Redis URL
        masked_redis = self.REDIS_URL
        if "@" in masked_redis:
            scheme_user, host_db = masked_redis.rsplit("@", 1)
            if ":" in scheme_user:
                scheme_u, _ = scheme_user.rsplit(":", 1)
                masked_redis = f"{scheme_u}:***@{host_db}"

        print(f"\n==================================================")
        print(f"   [MINDMESH PRODUCTION STARTUP CONFIG CHECK]")
        print(f"   [OK] NODE_ENV: {self.NODE_ENV}")
        print(f"   [OK] PORT: {self.PORT}")
        print(f"   [OK] DATABASE_URL: {masked_db}")
        print(f"   [OK] REDIS_URL: {masked_redis}")
        print(f"   [OK] GEMINI_API_KEY present: {bool(self.GEMINI_API_KEY)}")
        print(f"   [OK] SMTP_HOST: {self.SMTP_HOST}:{self.SMTP_PORT}")
        print(f"   [OK] SMTP_USERNAME: {self.SMTP_USERNAME}")
        print(f"   [OK] SMTP_FROM_EMAIL: {self.SMTP_FROM_EMAIL}")
        print(f"==================================================\n")

        missing = []
        if not user_ok:
            missing.append("SMTP_USERNAME")
        if not pass_ok:
            missing.append("SMTP_PASSWORD")
        if not from_ok:
            missing.append("SMTP_FROM_EMAIL")

        if missing:
            err_msg = (
                f"[CRITICAL CONFIG ERROR] Missing required SMTP environment variables: {', '.join(missing)}. "
                f"Please check your .env file and ensure SMTP_USERNAME and SMTP_PASSWORD are set."
            )
            print(f"\n{err_msg}\n", file=sys.stderr)
            raise RuntimeError(err_msg)

settings = Settings()
settings.validate_startup_config()



