from pathlib import Path
from typing import Optional, Any
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
        return s

    @field_validator("REDIS_URL", "JWT_SECRET", "JWT_REFRESH_SECRET", "GEMINI_API_KEY", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL", mode="before")
    @classmethod
    def clean_string_settings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().strip('\'"\\').strip()
        return v


    def validate_smtp_config(self) -> None:
        """Verifies required SMTP settings at startup and logs loaded configuration."""
        host_ok = bool(self.SMTP_HOST)
        port_ok = bool(self.SMTP_PORT)
        user_ok = bool(self.SMTP_USERNAME and self.SMTP_USERNAME.strip())
        pass_ok = bool(self.SMTP_PASSWORD and self.SMTP_PASSWORD.strip())
        from_ok = bool(self.SMTP_FROM_EMAIL and self.SMTP_FROM_EMAIL.strip())

        print(f"\n==================================================")
        print(f"   [BACKEND STARTUP SMTP CONFIG CHECK]")
        print(f"   [OK] SMTP_HOST loaded: {self.SMTP_HOST}")
        print(f"   [OK] SMTP_PORT loaded: {self.SMTP_PORT}")
        print(f"   [OK] SMTP_USERNAME loaded: {self.SMTP_USERNAME}")
        print(f"   [OK] SMTP_PASSWORD present: {pass_ok}")
        print(f"   [OK] SMTP_FROM_EMAIL loaded: {self.SMTP_FROM_EMAIL}")
        print(f"   [OK] SMTP_USE_TLS loaded: {self.SMTP_USE_TLS}")
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
settings.validate_smtp_config()


