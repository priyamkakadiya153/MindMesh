from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timedelta
import uuid
import hashlib
import secrets
from typing import Optional, Dict, Any
from fastapi import HTTPException, status

from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

from .repository import AuthRepository
from .schemas import UserRegister, UserLogin
from .security import get_password_hash, verify_password, validate_password_strength
from .firebase_auth import verify_firebase_id_token
from .email_service import EmailVerificationService, EmailService
from .utils import normalize_phone_number, validate_and_normalize_phone_number
from ..core.security import create_access_token, create_refresh_token
from ..models.user import User
from ..models.organization import Organization
from ..models.organization_member import OrganizationMember
from ..models.session import UserSession
from ..models.role import Role
from ..models.audit import AuditLog
from ..models.pending_registration import PendingRegistration
from .transports.email_transport import EmailOTPTransport
from .otp_service import mask_email
from ..workspace.models import Workspace, WorkspaceMember

class AuthService:
    def __init__(self):
        self.repo = AuthRepository()
        self.email_service = EmailVerificationService()
        self.smtp_service = EmailService()

    async def log_audit_event(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        action: str,
        organization_id: Optional[uuid.UUID] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Record enterprise audit trail event."""
        try:
            audit = AuditLog(
                user_id=user_id,
                action=action,
                organization_id=organization_id,
                details=details or {}
            )
            db.add(audit)
        except Exception:
            pass

    async def register(
        self,
        db: AsyncSession,
        user_in: UserRegister,
        device_name: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        """Alias for initiate_registration to trigger email OTP validation"""
        return await self.initiate_registration(db, user_in)

    async def initiate_registration(
        self,
        db: AsyncSession,
        user_in: UserRegister
    ) -> dict:
        if user_in.password:
            try:
                validate_password_strength(user_in.password)
            except ValueError as e:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

        clean_email = user_in.email.strip().lower()
        if await self.repo.get_user_by_email(db, clean_email):
            raise HTTPException(status_code=400, detail="This email address is already registered.")

        # Mandatory Mobile Number
        clean_phone = validate_and_normalize_phone_number(user_in.phone_number)

        existing_phone_user = await self.repo.get_user_by_phone_number(db, clean_phone)
        if existing_phone_user:
            raise HTTPException(status_code=400, detail="This mobile number is already registered.")

        first_name = (user_in.first_name or "").strip()
        last_name = (user_in.last_name or "").strip()
        if not first_name and user_in.display_name:
            parts = user_in.display_name.strip().split(" ", 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ""

        given_username = (user_in.username or "").strip()
        if given_username:
            if await self.repo.get_user_by_username(db, given_username):
                raise HTTPException(status_code=400, detail="This username is already taken.")
            username = given_username
        else:
            clean_first = "".join(c for c in first_name.lower() if c.isalnum())
            clean_last = "".join(c for c in last_name.lower() if c.isalnum())
            
            if clean_first and clean_last:
                base_username = f"{clean_first}.{clean_last}"
            elif clean_first:
                base_username = clean_first
            else:
                email_prefix = clean_email.split("@")[0]
                base_username = "".join(c for c in email_prefix.lower() if c.isalnum()) or "user"

            candidate = base_username
            counter = 1
            while True:
                existing_user = await self.repo.get_user_by_username(db, candidate)
                stmt = select(PendingRegistration).where(
                    PendingRegistration.username == candidate,
                    PendingRegistration.is_used == False
                )
                pending_res = await db.execute(stmt)
                existing_pending = pending_res.scalar_one_or_none()

                if not existing_user and not existing_pending:
                    username = candidate
                    break

                counter += 1
                if counter <= 10:
                    candidate = f"{base_username}{counter}"
                else:
                    candidate = f"{base_username}-{secrets.token_hex(2)}"

        now = datetime.utcnow()

        # Rate Limit / Cooldown check: 60 seconds
        existing_stmt = select(PendingRegistration).where(
            (PendingRegistration.email == clean_email) | (PendingRegistration.phone_number == clean_phone),
            PendingRegistration.is_used == False
        ).order_by(PendingRegistration.created_at.desc())
        existing_res = await db.execute(existing_stmt)
        latest_pending = existing_res.scalars().first()

        if latest_pending:
            time_since_creation = (now - latest_pending.created_at).total_seconds()
            if time_since_creation < 60:
                remaining_cooldown = int(60 - time_since_creation)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Please wait {remaining_cooldown} seconds before requesting a new code."
                )
            latest_pending.is_used = True
            db.add(latest_pending)

        # Generate secure 6-digit OTP code and SHA-256 hash
        plain_otp = f"{secrets.randbelow(900000) + 100000:06d}"
        otp_hash = hashlib.sha256(plain_otp.strip().encode("utf-8")).hexdigest()
        registration_token = f"reg_tok_{uuid.uuid4().hex}"
        hashed_pwd = get_password_hash(user_in.password) if user_in.password else ""
        expires_at = now + timedelta(minutes=5)

        new_pending = PendingRegistration(
            email=clean_email,
            username=username,
            hashed_password=hashed_pwd,
            phone_number=clean_phone,
            first_name=first_name,
            last_name=last_name,
            registration_token=registration_token,
            otp_hash=otp_hash,
            expires_at=expires_at,
            attempt_count=0,
            is_used=False,
            created_at=now,
            updated_at=now
        )
        db.add(new_pending)
        await db.commit()

        # Deliver OTP email via transport
        transport = EmailOTPTransport()
        sent = await transport.send_otp(
            recipient_identifier=clean_email,
            recipient_name=f"{first_name} {last_name}".strip() or username,
            otp_code=plain_otp
        )
        if not sent:
            # Clean up pending registration so user does not have an orphaned unverified session
            await db.delete(new_pending)
            await db.commit()
            res = getattr(transport, "last_delivery_result", None)
            if res and res.error_category == "unverified_sender":
                msg = "Email delivery failed: Sender email is not verified in Brevo. Please check EMAIL_FROM in Render settings."
            elif res and res.error_category in ("missing_api_key", "invalid_api_key"):
                msg = "Email delivery failed: Brevo API key is missing or invalid. Please check BREVO_API_KEY in Render settings."
            else:
                msg = "Unable to send verification email. Please check your email configuration or try again later."
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=msg
            )

        return {
            "status": "ok",
            "message": f"Verification code dispatched to {mask_email(clean_email)}",
            "email_masked": mask_email(clean_email),
            "registration_token": registration_token,
            "expires_in_seconds": 300,
            "resend_cooldown_seconds": 60,
        }



    async def resend_registration_otp(
        self,
        db: AsyncSession,
        registration_token: str
    ) -> dict:
        now = datetime.utcnow()
        stmt = select(PendingRegistration).where(
            PendingRegistration.registration_token == registration_token,
            PendingRegistration.is_used == False
        )
        res = await db.execute(stmt)
        pending = res.scalar_one_or_none()

        if not pending:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired registration session. Please start registration again."
            )

        if pending.expires_at < now:
            pending.is_used = True
            db.add(pending)
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration session has expired. Please start registration again."
            )

        time_since_creation = (now - pending.updated_at).total_seconds()
        if time_since_creation < 60:
            remaining = int(60 - time_since_creation)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting a new code."
            )

        plain_otp = f"{secrets.randbelow(900000) + 100000:06d}"
        pending.otp_hash = hashlib.sha256(plain_otp.strip().encode("utf-8")).hexdigest()
        pending.attempt_count = 0
        pending.updated_at = now
        db.add(pending)
        await db.commit()

        transport = EmailOTPTransport()
        sent = await transport.send_otp(
            recipient_identifier=pending.email,
            recipient_name=f"{pending.first_name} {pending.last_name}".strip() or pending.username,
            otp_code=plain_otp
        )
        if not sent:
            res = getattr(transport, "last_delivery_result", None)
            if res and res.error_category == "unverified_sender":
                msg = "Email delivery failed: Sender email is not verified in Brevo. Please check EMAIL_FROM in Render settings."
            elif res and res.error_category in ("missing_api_key", "invalid_api_key"):
                msg = "Email delivery failed: Brevo API key is missing or invalid. Please check BREVO_API_KEY in Render settings."
            else:
                msg = f"Unable to send verification email to {mask_email(pending.email)}. Please try again later."
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=msg
            )

        return {
            "status": "ok",
            "message": f"A new verification code has been dispatched to {mask_email(pending.email)}",
            "email_masked": mask_email(pending.email),
            "registration_token": registration_token,
            "resend_cooldown_seconds": 60,
        }



    async def complete_registration(
        self,
        db: AsyncSession,
        registration_token: str,
        code: str,
        device_name: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        clean_code = code.strip()
        if len(clean_code) != 6 or not clean_code.isdigit():
            raise HTTPException(status_code=400, detail="Verification code must be a 6-digit number.")

        now = datetime.utcnow()
        stmt = select(PendingRegistration).where(
            PendingRegistration.registration_token == registration_token,
            PendingRegistration.is_used == False
        )
        res = await db.execute(stmt)
        pending = res.scalar_one_or_none()

        if not pending:
            raise HTTPException(status_code=400, detail="Invalid or expired verification session.")

        if pending.expires_at < now:
            pending.is_used = True
            db.add(pending)
            await db.commit()
            raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new code.")

        pending.attempt_count += 1
        pending.updated_at = now

        if pending.attempt_count > 3:
            pending.is_used = True
            db.add(pending)
            await db.commit()
            raise HTTPException(status_code=400, detail="Maximum verification attempts exceeded. Please request a new code.")

        input_hash = hashlib.sha256(clean_code.encode("utf-8")).hexdigest()
        if input_hash != pending.otp_hash:
            db.add(pending)
            await db.commit()
            attempts_left = max(0, 3 - pending.attempt_count)
            if attempts_left == 0:
                pending.is_used = True
                db.add(pending)
                await db.commit()
                raise HTTPException(status_code=400, detail="Invalid verification code. Maximum attempts reached. Please request a new code.")
            raise HTTPException(status_code=400, detail=f"Invalid verification code. {attempts_left} attempt(s) remaining.")


        # Re-check uniqueness in case another user registered while OTP window was open
        if await self.repo.get_user_by_email(db, pending.email):
            raise HTTPException(status_code=400, detail="This email address is already registered.")
        if await self.repo.get_user_by_phone_number(db, pending.phone_number):
            raise HTTPException(status_code=400, detail="This mobile number is already registered.")
        if await self.repo.get_user_by_username(db, pending.username):
            raise HTTPException(status_code=400, detail="This username is already taken.")

        # Mark pending record as used
        pending.is_used = True
        db.add(pending)

        base_org_slug = f"{pending.username}-personal-org"
        org_slug = base_org_slug
        counter = 1
        while True:
            org_stmt = select(Organization).where(Organization.slug == org_slug)
            org_res = await db.execute(org_stmt)
            if not org_res.scalar_one_or_none():
                break
            counter += 1
            if counter <= 5:
                org_slug = f"{base_org_slug}-{counter}"
            else:
                org_slug = f"{base_org_slug}-{secrets.token_hex(2)}"

        new_user = User(
            email=pending.email,
            username=pending.username,
            hashed_password=pending.hashed_password,
            phone_number=pending.phone_number,
            first_name=pending.first_name,
            last_name=pending.last_name,
            is_verified=True,
            is_phone_verified=True,
            last_login_at=now
        )

        try:
            await self.repo.create_user(db, new_user)
            
            personal_org = Organization(
                name=f"{pending.username}'s Personal Org",
                slug=org_slug,
                owner_id=new_user.id
            )
            db.add(personal_org)
            await db.flush()

            role_stmt = select(Role).where(Role.name == "SUPER_ADMIN")
            role_res = await db.execute(role_stmt)
            role = role_res.scalar_one_or_none()
            if not role:
                role = Role(name="SUPER_ADMIN", description="Default Super Admin Role")
                db.add(role)
                await db.flush()

            member = OrganizationMember(
                organization_id=personal_org.id,
                user_id=new_user.id,
                role="OWNER",
                role_id=role.id
            )
            db.add(member)

            workspace = Workspace(
                name="Primary Workspace",
                slug="primary-workspace",
                organization_id=personal_org.id,
                created_by=new_user.id
            )
            db.add(workspace)
            await db.flush()

            ws_member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=new_user.id,
                role="OWNER"
            )
            db.add(ws_member)

            new_user.current_organization_id = personal_org.id
            new_user.current_workspace_id = workspace.id

            session_id = uuid.uuid4()
            db_session = UserSession(
                id=session_id,
                user_id=new_user.id,
                refresh_token_hash="",
                device_name=device_name,
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=now + timedelta(days=30),
                revoked=False
            )

            access_token = create_access_token(
                subject=new_user.id,
                org_id=personal_org.id,
                workspace_id=workspace.id,
                role=role.name,
                session_id=session_id
            )
            refresh_token = create_refresh_token(
                subject=new_user.id,
                org_id=personal_org.id,
                workspace_id=workspace.id,
                role=role.name,
                session_id=session_id
            )

            db_session.refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            await self.repo.save_session(db, db_session)
            await self.log_audit_event(db, new_user.id, "auth.register", personal_org.id, {"ip": ip_address, "device": device_name})

            await db.commit()
            await db.refresh(new_user)
        except HTTPException:
            await db.rollback()
            raise
        except SQLAlchemyError as db_err:
            await db.rollback()
            logger.exception(f"Database error during complete registration for {pending.email}: {db_err}")
            raise HTTPException(status_code=400, detail="Unable to create your account. Please try again.")

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": new_user
        }

    async def create_user_session(
        self,
        db: AsyncSession,
        user: User,
        device_name: str = None,
        ip_address: str = None,
        user_agent: str = None,
        audit_action: str = "auth.login"
    ) -> dict:
        now = datetime.utcnow()
        user.last_login_at = now

        if not user.current_organization_id:
            from ..organizations.service import OrganizationService
            await OrganizationService().ensure_user_personal_org(db, user)

        db.add(user)

        role_name = "MEMBER"
        if user.current_organization_id:
            from ..models.organization_member import OrganizationMember
            role_stmt = select(OrganizationMember).where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == user.current_organization_id
            )
            role_res = await db.execute(role_stmt)
            mem_obj = role_res.scalar_one_or_none()
            if mem_obj and mem_obj.role:
                role_name = mem_obj.role

        session_id = uuid.uuid4()
        db_session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash="",
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=now + timedelta(days=30),
            revoked=False
        )

        access_token = create_access_token(
            subject=user.id,
            org_id=user.current_organization_id,
            workspace_id=user.current_workspace_id,
            role=role_name,
            session_id=session_id
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            org_id=user.current_organization_id,
            workspace_id=user.current_workspace_id,
            role=role_name,
            session_id=session_id
        )

        db_session.refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.repo.save_session(db, db_session)
        await self.log_audit_event(db, user.id, audit_action, user.current_organization_id, {"ip": ip_address, "device": device_name})
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    async def login(
        self,
        db: AsyncSession,
        login_in: UserLogin,
        device_name: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        user = await self.repo.get_user_by_email(db, login_in.email)
        if not user or not verify_password(login_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await self.create_user_session(db, user, device_name, ip_address, user_agent, "auth.login")

    async def firebase_login(
        self,
        db: AsyncSession,
        id_token: str,
        device_name: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        decoded = verify_firebase_id_token(id_token)
        firebase_uid = decoded.get("uid")
        phone_number = decoded.get("phone_number")

        if not firebase_uid:
            raise HTTPException(status_code=400, detail="Invalid Firebase Token: missing uid")

        # Try finding user by firebase_uid
        user = await self.repo.get_user_by_firebase_uid(db, firebase_uid)

        # If not found by firebase_uid, try finding user by phone_number
        if not user and phone_number:
            user = await self.repo.get_user_by_phone_number(db, phone_number.strip())

        now = datetime.utcnow()

        if not user:
            # Auto-register user with mobile number/firebase uid
            clean_phone = phone_number.strip().replace("+", "").replace("-", "").replace(" ", "") if phone_number else firebase_uid[:10]
            generated_username = f"user_{clean_phone[-6:]}_{secrets.token_hex(2)}"
            dummy_password = f"P@ssw0rd!_{secrets.token_hex(8)}"

            clean_email = f"{clean_phone}@mobile.mindmesh.internal"
            hashed_pwd = get_password_hash(dummy_password)
            user = User(
                email=clean_email,
                username=generated_username,
                hashed_password=hashed_pwd,
                phone_number=phone_number.strip() if phone_number else None,
                first_name="Firebase",
                last_name="User",
                is_verified=True,
                is_phone_verified=True,
                firebase_uid=firebase_uid,
                last_login_at=now
            )
            await self.repo.create_user(db, user)

            org_slug = f"{generated_username}-personal-org"
            personal_org = Organization(
                name=f"{generated_username}'s Personal Org",
                slug=org_slug,
                owner_id=user.id
            )
            db.add(personal_org)
            await db.flush()

            role_stmt = select(Role).where(Role.name == "SUPER_ADMIN")
            role_res = await db.execute(role_stmt)
            role = role_res.scalar_one_or_none()
            if not role:
                role = Role(name="SUPER_ADMIN", description="Default Super Admin Role")
                db.add(role)
                await db.flush()

            member = OrganizationMember(
                organization_id=personal_org.id,
                user_id=user.id,
                role="OWNER",
                role_id=role.id
            )
            db.add(member)

            workspace = Workspace(
                name="Primary Workspace",
                slug="primary-workspace",
                organization_id=personal_org.id,
                created_by=user.id
            )
            db.add(workspace)
            await db.flush()

            ws_member = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=user.id,
                role="OWNER"
            )
            db.add(ws_member)

            user.current_organization_id = personal_org.id
            user.current_workspace_id = workspace.id
            db.add(user)
            await db.commit()

        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
        user.is_phone_verified = True
        user.last_login_at = now
        db.add(user)

        role_name = "MEMBER"
        if user.current_organization_id:
            role_stmt = select(Role).join(OrganizationMember).where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == user.current_organization_id
            )
            role_res = await db.execute(role_stmt)
            role_obj = role_res.scalar_one_or_none()
            if role_obj:
                role_name = role_obj.name

        session_id = uuid.uuid4()
        db_session = UserSession(
            id=session_id,
            user_id=user.id,
            refresh_token_hash="",
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=now + timedelta(days=30),
            revoked=False
        )

        access_token = create_access_token(
            subject=user.id,
            org_id=user.current_organization_id,
            workspace_id=user.current_workspace_id,
            role=role_name,
            session_id=session_id
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            org_id=user.current_organization_id,
            workspace_id=user.current_workspace_id,
            role=role_name,
            session_id=session_id
        )

        db_session.refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.repo.save_session(db, db_session)
        await self.log_audit_event(db, user.id, "auth.firebase_login", user.current_organization_id, {"firebase_uid": firebase_uid, "phone": phone_number})
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    async def refresh_tokens(
        self,
        db: AsyncSession,
        token: str,
        device_name: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> dict:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db_session = await self.repo.get_session_by_hash(db, token_hash)
        
        if not db_session or db_session.expires_at < datetime.utcnow() or db_session.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please sign in again."
            )

        user_stmt = select(User).where(User.id == db_session.user_id)
        user_res = await db.execute(user_stmt)
        user = user_res.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your session has expired. Please sign in again."
            )

        role_name = "MEMBER"
        if user.current_organization_id:
            role_stmt = select(Role).join(OrganizationMember).where(
                OrganizationMember.user_id == user.id,
                OrganizationMember.organization_id == user.current_organization_id
            )
            role_res = await db.execute(role_stmt)
            role_obj = role_res.scalar_one_or_none()
            if role_obj:
                role_name = role_obj.name

        db_session.revoked = True
        db_session.updated_at = datetime.utcnow()
        db.add(db_session)

        new_session_id = uuid.uuid4()
        new_session = UserSession(
            id=new_session_id,
            user_id=user.id,
            refresh_token_hash="",
            device_name=device_name or db_session.device_name,
            ip_address=ip_address or db_session.ip_address,
            user_agent=user_agent or db_session.user_agent,
            expires_at=datetime.utcnow() + timedelta(days=30),
            revoked=False
        )

        access_token = create_access_token(
            subject=user.id,
            org_id=user.current_organization_id,
            workspace_id=user.current_workspace_id,
            role=role_name,
            session_id=new_session_id
        )
        refresh_token = create_refresh_token(
            subject=user.id,
            org_id=user.current_organization_id,
            workspace_id=user.current_workspace_id,
            role=role_name,
            session_id=new_session_id
        )

        new_session.refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        await self.repo.save_session(db, new_session)
        await db.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def logout(self, db: AsyncSession, token: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        db_session = await self.repo.get_session_by_hash(db, token_hash)
        if db_session:
            db_session.revoked = True
            db_session.updated_at = datetime.utcnow()
            db.add(db_session)
            await db.commit()
            return True
        return False

    async def logout_all(self, db: AsyncSession, user_id: uuid.UUID) -> bool:
        sessions = await self.repo.list_active_sessions(db, user_id)
        for s in sessions:
            s.revoked = True
            s.updated_at = datetime.utcnow()
            db.add(s)
        await db.commit()
        return True

    async def request_password_reset(self, db: AsyncSession, email: str) -> bool:
        clean_email = email.strip().lower()
        user = await self.repo.get_user_by_email(db, clean_email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account found with this email address."
            )

        token, code = await self.email_service.send_email_verification(db, user)
        await self.smtp_service.send_password_reset_email(
            recipient_email=user.email,
            user_name=user.full_name or user.email,
            code=code,
            token=token
        )
        return True

    async def reset_password(self, db: AsyncSession, token_or_code: str, new_password: str) -> bool:
        validate_password_strength(new_password)
        user = await self.email_service.verify_email_token(db, token_or_code)
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.add(user)
        # Revoke existing active sessions for security
        await self.logout_all(db, user.id)
        await self.log_audit_event(db, user.id, "auth.password_reset")
        await db.commit()
        return True

    async def change_password(self, db: AsyncSession, user: User, current_password: str, new_password: str) -> bool:
        if not verify_password(current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect current password.")
        validate_password_strength(new_password)
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        db.add(user)
        await self.log_audit_event(db, user.id, "auth.password_change")
        await db.commit()
        return True

    async def export_user_data(self, db: AsyncSession, user: User) -> Dict[str, Any]:
        """Generate compliance data dump for user."""
        active_sessions = await self.repo.list_active_sessions(db, user.id)
        return {
            "account": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "phone_number": user.phone_number,
                "bio": user.bio,
                "timezone": user.timezone,
                "language": user.language,
                "theme": user.theme,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat() if user.created_at else None
            },
            "active_sessions_count": len(active_sessions),
            "export_timestamp": datetime.utcnow().isoformat()
        }

    async def delete_account(self, db: AsyncSession, user: User) -> bool:
        """Soft delete or permanently remove user account."""
        user.is_active = False
        user.email = f"deleted_{user.id}_{user.email}"
        user.username = f"deleted_{user.id}"
        user.updated_at = datetime.utcnow()
        db.add(user)
        await self.logout_all(db, user.id)
        await db.commit()
        return True
