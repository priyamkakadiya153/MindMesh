import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
import logging

from ..models.user import User
from ..models.otp import OtpCode
from .transports.base import BaseOTPTransport
from .transports.email_transport import EmailOTPTransport

from .utils import normalize_phone_number

logger = logging.getLogger(__name__)

def mask_email(email: str) -> str:
    """Helper to mask recipient email for frontend display (e.g. u***1@example.com)"""
    if not email or "@" not in email:
        return "****"
    user_part, domain_part = email.split("@", 1)
    if len(user_part) <= 2:
        masked_user = user_part[0] + "*"
    else:
        masked_user = user_part[0] + "*" * (len(user_part) - 2) + user_part[-1]
    return f"{masked_user}@{domain_part}"

class OTPService:
    """
    Core Knowledge Intelligence System OTP Service.
    Enforces cryptographically secure 6-digit OTP generation, SHA-256 hash persistence,
    5-minute expiration, max 3 verification attempts, and 60s resend cooldown.
    Delivery is delegated to a pluggable transport (defaulting to EmailOTPTransport).
    """

    EXPIRY_MINUTES = 5
    MAX_ATTEMPTS = 3
    RESEND_COOLDOWN_SECONDS = 60

    def __init__(self, transport: Optional[BaseOTPTransport] = None):
        self.transport = transport or EmailOTPTransport()

    @staticmethod
    def generate_otp_code() -> str:
        """Generates a secure 6-digit numeric OTP"""
        return f"{secrets.randbelow(900000) + 100000:06d}"

    @staticmethod
    def hash_otp(code: str) -> str:
        """Computes SHA-256 hex digest of plain OTP string"""
        return hashlib.sha256(code.strip().encode("utf-8")).hexdigest()

    async def _find_user_by_phone(self, db: AsyncSession, phone_number: str) -> Optional[User]:
        normalized = normalize_phone_number(phone_number)
        if not normalized:
            return None

        user_stmt = select(User).where(User.phone_number == normalized)
        res = await db.execute(user_stmt)
        user = res.scalar_one_or_none()
        if user:
            return user

        all_users_stmt = select(User).where(User.phone_number.isnot(None))
        all_res = await db.execute(all_users_stmt)
        all_users = all_res.scalars().all()
        for u in all_users:
            if u.phone_number and normalize_phone_number(u.phone_number) == normalized:
                return u
        return None

    async def request_phone_otp(self, db: AsyncSession, phone_number: str) -> Dict[str, Any]:
        """
        Processes OTP request for a mobile number.
        Looks up user -> checks email existence -> checks resend cooldown ->
        invalidates old OTPs -> generates code & SHA-256 hash -> saves in database -> delivers via transport.
        """
        logger.info(f"[OTP FLOW] 1. Request received for phone number: {phone_number}")
        now = datetime.utcnow()
        user = await self._find_user_by_phone(db, phone_number)

        if not user:
            logger.warning(f"[OTP FLOW] User lookup failed for phone: {phone_number}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found associated with this mobile number."
            )

        logger.info(f"[OTP FLOW] 2. User located: ID={user.id}, email={user.email}")

        if not user.email or not user.email.strip():
            logger.warning(f"[OTP FLOW] User {user.id} has no registered email address.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account does not have a registered email address to receive verification codes."
            )

        # 3. Check 60-second resend cooldown
        latest_otp_stmt = (
            select(OtpCode)
            .where(
                OtpCode.user_id == user.id,
                OtpCode.purpose == "phone_login",
                OtpCode.is_used == False
            )
            .order_by(OtpCode.created_at.desc())
        )
        latest_res = await db.execute(latest_otp_stmt)
        latest_otp = latest_res.scalars().first()

        if latest_otp:
            time_since_creation = (now - latest_otp.created_at).total_seconds()
            if time_since_creation < self.RESEND_COOLDOWN_SECONDS:
                remaining_cooldown = int(self.RESEND_COOLDOWN_SECONDS - time_since_creation)
                logger.info(f"[OTP FLOW] Resend cooldown active. Remaining: {remaining_cooldown}s")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {remaining_cooldown} seconds before requesting a new OTP."
                )

        # 4. Invalidate any existing active OTPs for this user
        invalidate_stmt = (
            update(OtpCode)
            .where(
                OtpCode.user_id == user.id,
                OtpCode.purpose == "phone_login",
                OtpCode.is_used == False
            )
            .values(is_used=True, updated_at=now)
        )
        await db.execute(invalidate_stmt)

        # 5. Generate new 6-digit code and SHA-256 hash
        plain_otp = self.generate_otp_code()
        hashed_otp = self.hash_otp(plain_otp)
        expires_at = now + timedelta(minutes=self.EXPIRY_MINUTES)
        logger.info(f"[OTP FLOW] 3. Generated secure 6-digit OTP code")

        # 6. Store record in `otp_codes`
        otp_record = OtpCode(
            user_id=user.id,
            otp_hash=hashed_otp,
            purpose="phone_login",
            expires_at=expires_at,
            attempt_count=0,
            is_used=False,
            created_at=now,
            updated_at=now
        )
        try:
            db.add(otp_record)
            await db.commit()
            logger.info(f"[OTP FLOW] 4. OTP record saved to database (user_id={user.id})")
        except SQLAlchemyError as db_err:
            await db.rollback()
            logger.exception(f"[OTP FLOW ERROR] Database transaction failed while saving OTP: {db_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database transaction failed while saving verification code."
            )

        # 7. Deliver OTP to recipient's registered email using transport
        display_name = user.full_name or user.email
        logger.info(f"[OTP FLOW] 5. Initiating transport email delivery to {user.email}")
        sent_successfully = await self.transport.send_otp(
            recipient_identifier=user.email,
            recipient_name=display_name,
            otp_code=plain_otp
        )

        if not sent_successfully:
            logger.error(f"[OTP FLOW ERROR] Delivery transport reported failure for user {user.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to deliver verification code via Gmail SMTP to {user.email}. Please verify SMTP configuration."
            )

        logger.info(f"[OTP FLOW] 6. OTP request process completed successfully for user {user.id}")
        return {
            "status": "ok",
            "message": f"Verification code dispatched to {mask_email(user.email)}",
            "email_masked": mask_email(user.email),
            "expires_in_seconds": self.EXPIRY_MINUTES * 60,
            "resend_cooldown_seconds": self.RESEND_COOLDOWN_SECONDS
        }

    async def verify_phone_otp(
        self, db: AsyncSession, phone_number: str, code: str
    ) -> Tuple[User, OtpCode]:
        """
        Verifies the user's OTP code.
        Validates hash, expiry date, attempt counts. Marks OTP as used upon success.
        """
        clean_phone = phone_number.strip()
        clean_code = code.strip()
        now = datetime.utcnow()

        if len(clean_code) != 6 or not clean_code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code must be a 6-digit number."
            )

        # 1. Lookup user
        user = await self._find_user_by_phone(db, phone_number)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found associated with this mobile number."
            )

        # 2. Find active OTP record
        otp_stmt = (
            select(OtpCode)
            .where(
                OtpCode.user_id == user.id,
                OtpCode.purpose == "phone_login",
                OtpCode.is_used == False
            )
            .order_by(OtpCode.created_at.desc())
        )
        otp_res = await db.execute(otp_stmt)
        otp_record = otp_res.scalars().first()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification session. Please request a new code."
            )

        # 3. Check Expiration
        if otp_record.expires_at < now:
            otp_record.is_used = True
            otp_record.updated_at = now
            db.add(otp_record)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired. Please request a new code."
            )

        # 4. Check & increment attempt count
        otp_record.attempt_count += 1
        otp_record.updated_at = now

        if otp_record.attempt_count > self.MAX_ATTEMPTS:
            otp_record.is_used = True
            db.add(otp_record)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum verification attempts exceeded. Please request a new code."
            )

        # 5. Verify SHA-256 Hash
        input_hash = self.hash_otp(clean_code)
        if input_hash != otp_record.otp_hash:
            db.add(otp_record)
            await db.commit()
            attempts_left = max(0, self.MAX_ATTEMPTS - otp_record.attempt_count)
            if attempts_left == 0:
                otp_record.is_used = True
                db.add(otp_record)
                await db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid verification code. Maximum attempts reached. Please request a new code."
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification code. {attempts_left} attempt(s) remaining."
            )

        # 6. Success: Mark OTP as used and update user flags
        otp_record.is_used = True
        user.is_phone_verified = True
        user.last_login_at = now
        user.updated_at = now

        db.add(otp_record)
        db.add(user)
        await db.commit()

        return user, otp_record

    async def cleanup_expired_otps(self, db: AsyncSession) -> int:
        """Purges old expired OTP records from database"""
        now = datetime.utcnow()
        stmt = (
            update(OtpCode)
            .where((OtpCode.expires_at < now) | (OtpCode.is_used == True))
            .values(is_used=True)
        )
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount
