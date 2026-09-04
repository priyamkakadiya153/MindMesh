import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import make_msgid, formatdate
import asyncio
import secrets
from datetime import datetime, timedelta

from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
import logging

from ..models.user import User
from ..models.verification import EmailVerification
from ..core.config import settings

logger = logging.getLogger(__name__)

class EmailVerificationService:
    """Legacy Email Link / Token verification service"""
    TOKEN_EXPIRATION_HOURS = 24

    @staticmethod
    def generate_token_and_code() -> Tuple[str, str]:
        token = secrets.token_urlsafe(32)
        code = f"{secrets.randbelow(900000) + 100000:06d}"
        return token, code

    async def send_email_verification(self, db: AsyncSession, user: User) -> Tuple[str, str]:
        token, code = self.generate_token_and_code()
        expires_at = datetime.utcnow() + timedelta(hours=self.TOKEN_EXPIRATION_HOURS)

        verification = EmailVerification(
            user_id=user.id,
            email=user.email,
            token=token,
            code=code,
            expires_at=expires_at,
            is_used=False
        )
        db.add(verification)
        await db.commit()

        print(f"\n==========================================")
        print(f"   [DEV EMAIL] Verification Link sent to {user.email}:")
        print(f"   Verification Code: {code}")
        print(f"   Verification Token: {token}")
        print(f"==========================================\n")
        logger.info(f"Generated email verification token for user {user.id}")
        return token, code

    async def verify_email_token(self, db: AsyncSession, token_or_code: str) -> User:
        now = datetime.utcnow()
        stmt = select(EmailVerification).where(
            (EmailVerification.token == token_or_code) | (EmailVerification.code == token_or_code),
            EmailVerification.is_used == False
        ).order_by(EmailVerification.created_at.desc())
        res = await db.execute(stmt)
        record = res.scalars().first()

        if not record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token."
            )

        if record.expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification link has expired. Please request a new verification email."
            )

        record.is_used = True
        record.updated_at = now
        db.add(record)

        user_stmt = select(User).where(User.id == record.user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User associated with verification token not found.")

        user.is_verified = True
        user.updated_at = now
        db.add(user)
        await db.commit()

        return user


import socket

def mask_email(email: str) -> str:
    """Safely masks an email address for logs (e.g. p***a@domain.com)."""
    if not email or "@" not in email:
        return "***"
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"


from .providers.factory import get_email_provider
from .providers.base import EmailDeliveryResult, BaseEmailProvider
from .providers.brevo import mask_email


class EmailService:
    """
    Enterprise Email Service managing outbound email transmission through configured providers
    (Brevo HTTP REST API over Port 443 in production, SMTP in local development).
    """

    def __init__(self, provider: Optional[BaseEmailProvider] = None):
        self.provider = provider or get_email_provider()

    async def send_otp_email_detailed(
        self,
        recipient_email: str,
        user_name: str,
        otp_code: str
    ) -> EmailDeliveryResult:
        """
        Dispatches verification OTP email and returns structured EmailDeliveryResult
        with error categorization.
        """
        result = await self.provider.send_verification_email(
            recipient_email=recipient_email,
            recipient_name=user_name,
            otp_code=otp_code
        )

        # If primary provider failed and fallback SMTP is available (and not already tried), try SMTP fallback
        if not result.success and result.provider == "brevo" and settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            logger.info("provider=brevo failed; attempting SMTP fallback for %s...", mask_email(recipient_email))
            from .providers.smtp import SMTPEmailProvider
            smtp_provider = SMTPEmailProvider()
            fallback_res = await smtp_provider.send_verification_email(
                recipient_email=recipient_email,
                recipient_name=user_name,
                otp_code=otp_code
            )
            if fallback_res.success:
                return fallback_res

        return result

    async def send_otp_email(self, recipient_email: str, user_name: str, otp_code: str) -> bool:
        """Standard boolean method for OTP transport delivery."""
        res = await self.send_otp_email_detailed(recipient_email, user_name, otp_code)
        return res.success

    async def send_password_reset_email(self, recipient_email: str, user_name: str, code: str, token: str) -> bool:
        """Dispatches password reset instructions email."""
        res = await self.provider.send_password_reset_email(
            recipient_email=recipient_email,
            recipient_name=user_name,
            code=code,
            token=token
        )
        return res.success

    async def verify_sender_status(self) -> dict:
        """Checks configuration readiness and sender authorization with the active provider."""
        return await self.provider.verify_sender_status()



