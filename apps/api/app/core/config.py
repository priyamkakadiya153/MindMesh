from pathlib import Path
from typing import Optional, Any
from urllib.parse import quote_plus, unquote
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys
import os

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
        case_sensitive=False,
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

    # Email Provider Configuration
    EMAIL_PROVIDER: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_FROM_NAME: str = "MindMesh"
    BREVO_API_KEY: Optional[str] = None


    # SMTP Configuration (Fallback / Local Dev)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_NAME: str = "MindMesh"
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True
    RESEND_API_KEY: Optional[str] = None
    RESEND_FROM_EMAIL: Optional[str] = None
    SENDGRID_API_KEY: Optional[str] = None




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

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_connection(cls, v: Any) -> str:
        if not v:
            return "redis://localhost:6379"
        s = str(v).strip().strip('\'"\\').strip()
        if "redis-cli" in s or "-u " in s:
            import re
            m = re.search(r"(rediss?://[^\s'\"]+)", s)
            if m:
                s = m.group(1)
        if not any(s.startswith(prefix) for prefix in ["redis://", "rediss://", "unix://"]):
            print(f"[CONFIG WARNING] Invalid REDIS_URL scheme '{s}', defaulting to redis://localhost:6379.")
            return "redis://localhost:6379"
        return s


    @field_validator(
        "JWT_SECRET", "JWT_REFRESH_SECRET", "GEMINI_API_KEY",
        "EMAIL_PROVIDER", "EMAIL_FROM", "EMAIL_FROM_NAME",
        "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM_EMAIL", "SMTP_FROM_NAME",
        "RESEND_API_KEY", "RESEND_FROM_EMAIL", "BREVO_API_KEY", "SENDGRID_API_KEY",
        mode="before"
    )
    @classmethod
    def clean_string_settings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().strip('\'"\\').strip()
        return v

    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        # Direct fallback checks on os.environ in case environment variable was passed with unexpected casing
        if not self.BREVO_API_KEY:
            for k in ["BREVO_API_KEY", "brevo_api_key", "SENDINBLUE_API_KEY", "sendinblue_api_key"]:
                val = os.environ.get(k)
                if val and val.strip():
                    self.BREVO_API_KEY = val.strip().strip('\'"\\').strip()
                    break

        if not self.EMAIL_FROM:
            for k in ["EMAIL_FROM", "email_from", "SMTP_FROM_EMAIL", "smtp_from_email", "SMTP_USERNAME", "smtp_username"]:
                val = os.environ.get(k)
                if val and val.strip():
                    self.EMAIL_FROM = val.strip().strip('\'"\\').strip()
                    break

        if not self.EMAIL_FROM_NAME:
            for k in ["EMAIL_FROM_NAME", "email_from_name", "SMTP_FROM_NAME", "smtp_from_name"]:
                val = os.environ.get(k)
                if val and val.strip():
                    self.EMAIL_FROM_NAME = val.strip().strip('\'"\\').strip()
                    break

        if not self.EMAIL_PROVIDER:
            for k in ["EMAIL_PROVIDER", "email_provider"]:
                val = os.environ.get(k)
                if val and val.strip():
                    self.EMAIL_PROVIDER = val.strip().strip('\'"\\').strip().lower()
                    break

        # Harmonize EMAIL_FROM with SMTP_FROM_EMAIL and SMTP_USERNAME
        if not self.EMAIL_FROM:
            self.EMAIL_FROM = self.SMTP_FROM_EMAIL or self.SMTP_USERNAME
        if not self.SMTP_FROM_EMAIL and self.EMAIL_FROM:
            self.SMTP_FROM_EMAIL = self.EMAIL_FROM
        if not self.EMAIL_FROM_NAME:
            self.EMAIL_FROM_NAME = self.SMTP_FROM_NAME or "MindMesh"
        if not self.SMTP_FROM_NAME and self.EMAIL_FROM_NAME:
            self.SMTP_FROM_NAME = self.EMAIL_FROM_NAME

        # If EMAIL_PROVIDER is not set, default to brevo if BREVO_API_KEY is present, else smtp
        if not self.EMAIL_PROVIDER or not self.EMAIL_PROVIDER.strip():
            self.EMAIL_PROVIDER = "brevo" if self.BREVO_API_KEY else "smtp"

    def validate_startup_config(self) -> None:
        """Verifies required settings at startup and logs loaded configuration with passwords masked."""
        host_ok = bool(self.SMTP_HOST)
        port_ok = bool(self.SMTP_PORT)
        user_ok = bool(self.SMTP_USERNAME and self.SMTP_USERNAME.strip())
        pass_ok = bool(self.SMTP_PASSWORD and self.SMTP_PASSWORD.strip())
        from_ok = bool(self.EMAIL_FROM and self.EMAIL_FROM.strip())
        brevo_ok = bool(self.BREVO_API_KEY and self.BREVO_API_KEY.strip())
        brevo_prefix = "xkeysib-" if (self.BREVO_API_KEY and self.BREVO_API_KEY.startswith("xkeysib-")) else ("none" if not brevo_ok else "other")
        brevo_len = len(self.BREVO_API_KEY or "")
        has_http_email = bool(brevo_ok or self.RESEND_API_KEY or self.SENDGRID_API_KEY)

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
        print(f"   [OK] EMAIL_PROVIDER: {self.EMAIL_PROVIDER}")
        print(f"   [OK] BREVO_API_KEY present: {brevo_ok} (prefix={brevo_prefix}, length={brevo_len})")
        print(f"   [OK] EMAIL_FROM: {self.EMAIL_FROM}")
        print(f"   [OK] EMAIL_FROM_NAME: {self.EMAIL_FROM_NAME}")
        print(f"   [OK] RESEND_API_KEY present: {bool(self.RESEND_API_KEY)}")
        print(f"   [OK] SENDGRID_API_KEY present: {bool(self.SENDGRID_API_KEY)}")
        print(f"   [OK] SMTP_HOST: {self.SMTP_HOST}:{self.SMTP_PORT}")
        print(f"==================================================\n")

        missing = []
        if self.EMAIL_PROVIDER.lower() == "brevo":
            if not brevo_ok:
                missing.append("BREVO_API_KEY (required when EMAIL_PROVIDER=brevo)")
            if not from_ok:
                missing.append("EMAIL_FROM (must be a verified sender in Brevo, e.g. priyamakakadiya@gmail.com)")
        elif self.EMAIL_PROVIDER.lower() == "smtp":
            if not user_ok:
                missing.append("SMTP_USERNAME")
            if not pass_ok:
                missing.append("SMTP_PASSWORD")
            if not from_ok:
                missing.append("EMAIL_FROM (or SMTP_FROM_EMAIL)")
        else:
            if not (has_http_email or (user_ok and pass_ok)):
                missing.append("Valid email provider credentials (BREVO_API_KEY or SMTP)")

        if missing:
            err_msg = (
                f"[CRITICAL CONFIG ERROR] Missing required email delivery configuration: {', '.join(missing)}. "
                f"Please ensure either Brevo API credentials (BREVO_API_KEY and EMAIL_FROM) or SMTP credentials are set."
            )
            print(f"\n{err_msg}\n", file=sys.stderr)
            raise RuntimeError(err_msg)


settings = Settings()
settings.validate_startup_config()




