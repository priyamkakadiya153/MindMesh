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


class EmailService:
    """
    Enterprise Email Service supporting both HTTP REST APIs (Brevo, Resend, SendGrid)
    over Port 443 and standard TLS SMTP. Never swallows delivery failures or logs plaintext OTPs.
    """

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_name = settings.SMTP_FROM_NAME or "MindMesh"
        self.from_email = settings.SMTP_FROM_EMAIL or self.smtp_username or "auth@mindmesh.ai"
        self.resend_api_key = (getattr(settings, "RESEND_API_KEY", None) or os.getenv("RESEND_API_KEY", "") or "").strip()
        self.resend_from_email = getattr(settings, "RESEND_FROM_EMAIL", None) or os.getenv("RESEND_FROM_EMAIL", "")
        self.brevo_api_key = (getattr(settings, "BREVO_API_KEY", None) or os.getenv("BREVO_API_KEY", "") or "").strip()
        self.sendgrid_api_key = (getattr(settings, "SENDGRID_API_KEY", None) or os.getenv("SENDGRID_API_KEY", "") or "").strip()

    def _build_otp_email_html(self, user_name: str, otp_code: str) -> str:
        safe_name = user_name or "MindMesh User"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify your MindMesh email</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="min-width: 100%; background-color: #0f172a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 32px 32px 24px 32px; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">MindMesh</h1>
                            <p style="margin: 4px 0 0 0; color: #e0e7ff; font-size: 13px; font-weight: 500; opacity: 0.9;">Knowledge Intelligence System</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px;">
                            <h2 style="margin: 0 0 12px 0; color: #f8fafc; font-size: 18px; font-weight: 600;">Hello {safe_name},</h2>
                            <p style="margin: 0 0 24px 0; color: #94a3b8; font-size: 14px; line-height: 1.6;">
                                Your MindMesh email verification code is:
                            </p>
                            
                            <!-- Code Display Box -->
                            <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
                                <span style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 700; color: #818cf8; letter-spacing: 8px; display: inline-block;">{otp_code}</span>
                            </div>
                            
                            <p style="margin: 0 0 8px 0; color: #f59e0b; font-size: 13px; font-weight: 500; text-align: center;">
                                &#9200; This code expires in 5 minutes.
                            </p>
                            <p style="margin: 0 0 16px 0; color: #ef4444; font-size: 12px; font-weight: 500; text-align: center;">
                                Do not share this code with anyone. MindMesh will never ask for your code.
                            </p>
                            
                            <p style="margin: 24px 0 0 0; color: #64748b; font-size: 13px; line-height: 1.5; border-top: 1px solid #334155; padding-top: 20px;">
                                If you did not request this verification code, please ignore this email.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 32px; background-color: #0f172a; border-top: 1px solid #334155; text-align: center;">
                            <p style="margin: 0; color: #64748b; font-size: 12px;">Regards,<br><strong style="color: #94a3b8;">MindMesh Security Team</strong></p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    async def _send_brevo_api(self, recipient_email: str, user_name: str, subject: str, text_content: str, html_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Sends email via Brevo (Sendinblue) HTTP REST API over Port 443."""
        if not self.brevo_api_key:
            return False, None, "Brevo API key not configured"

        try:
            import httpx
            sender_email = self.from_email or "auth@mindmesh.ai"
            payload = {
                "sender": {"name": self.from_name, "email": sender_email},
                "to": [{"email": recipient_email, "name": user_name or "User"}],
                "subject": subject,
                "htmlContent": html_content,
                "textContent": text_content,
            }
            headers = {
                "api-key": self.brevo_api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("https://api.brevo.com/v3/smtp/email", headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    msg_id = resp.json().get("messageId", f"brevo-{secrets.token_hex(4)}")
                    return True, msg_id, None
                else:
                    return False, None, f"Brevo HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, None, f"Brevo request exception: {str(e)}"

    async def _send_resend_api(self, recipient_email: str, user_name: str, subject: str, text_content: str, html_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Sends email via Resend HTTP REST API over Port 443."""
        if not self.resend_api_key:
            return False, None, "Resend API key not configured"

        try:
            import httpx
            from_sender = self.resend_from_email or (f"{self.from_name} <{self.from_email}>" if "@" in self.from_email and not self.from_email.endswith("mindmesh.ai") else f"{self.from_name} <onboarding@resend.dev>")
            payload = {
                "from": from_sender,
                "to": [recipient_email],
                "subject": subject,
                "html": html_content,
                "text": text_content,
            }
            headers = {
                "Authorization": f"Bearer {self.resend_api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("https://api.resend.com/emails", headers=headers, json=payload)
                if resp.status_code in (200, 201):
                    msg_id = resp.json().get("id", f"resend-{secrets.token_hex(4)}")
                    return True, msg_id, None
                else:
                    return False, None, f"Resend HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, None, f"Resend request exception: {str(e)}"

    async def _send_sendgrid_api(self, recipient_email: str, user_name: str, subject: str, text_content: str, html_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Sends email via SendGrid HTTP REST API over Port 443."""
        if not self.sendgrid_api_key:
            return False, None, "SendGrid API key not configured"

        try:
            import httpx
            sender_email = self.from_email or "auth@mindmesh.ai"
            payload = {
                "personalizations": [{"to": [{"email": recipient_email, "name": user_name or "User"}]}],
                "from": {"email": sender_email, "name": self.from_name},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": text_content},
                    {"type": "text/html", "value": html_content},
                ]
            }
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post("https://api.sendgrid.com/v3/mail/send", headers=headers, json=payload)
                if resp.status_code in (200, 201, 202):
                    msg_id = resp.headers.get("X-Message-Id", f"sendgrid-{secrets.token_hex(4)}")
                    return True, msg_id, None
                else:
                    return False, None, f"SendGrid HTTP {resp.status_code}: {resp.text}"
        except Exception as e:
            return False, None, f"SendGrid request exception: {str(e)}"

    def _send_smtp_sync(self, recipient_email: str, subject: str, text_content: str, html_content: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Sends email via standard TLS SMTP connection."""
        if not self.smtp_username or not self.smtp_password:
            return False, None, "SMTP credentials missing"

        clean_username = self.smtp_username.strip()
        clean_password = self.smtp_password.replace(" ", "")

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = recipient_email
            msg["Date"] = formatdate(localtime=True)
            msg["Message-ID"] = make_msgid(domain="mindmesh.ai")

            part1 = MIMEText(text_content, "plain", "utf-8")
            part2 = MIMEText(html_content, "html", "utf-8")
            msg.attach(part1)
            msg.attach(part2)

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=12) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                server.login(clean_username, clean_password)
                refused = server.sendmail(self.from_email, [recipient_email], msg.as_string())
                if refused:
                    return False, None, f"SMTP server refused recipient: {refused}"

            return True, msg["Message-ID"], None
        except smtplib.SMTPAuthenticationError as auth_err:
            return False, None, f"SMTP Authentication failed: {auth_err}"
        except (smtplib.SMTPConnectError, socket.timeout, TimeoutError, OSError) as conn_err:
            return False, None, f"SMTP Connection/Timeout error: {conn_err}"
        except Exception as e:
            return False, None, f"SMTP Unexpected error: {str(e)}"

    async def send_otp_email(self, recipient_email: str, user_name: str, otp_code: str) -> bool:
        """
        Dispatches OTP email via configured providers in order of priority:
        1. Brevo HTTP API (Port 443)
        2. Resend HTTP API (Port 443)
        3. SendGrid HTTP API (Port 443)
        4. Standard TLS SMTP

        Safely logs masked recipients and provider statuses without leaking OTPs.
        Returns True if accepted by a provider, False otherwise. Never swallows errors.
        """
        safe_name = user_name or "MindMesh User"
        subject = "Verify your MindMesh email"
        text_content = (
            f"Hello {safe_name},\n\n"
            f"Your MindMesh verification code is: {otp_code}\n\n"
            f"This code expires in 5 minutes.\n"
            f"Do not share this code with anyone.\n\n"
            f"If you did not request this verification code, please ignore this email.\n\n"
            f"Regards,\nMindMesh Security Team"
        )
        html_content = self._build_otp_email_html(safe_name, otp_code)
        masked_dest = mask_email(recipient_email)

        logger.info(f"[OUTBOUND EMAIL ATTEMPT] Recipient: {masked_dest}, Purpose: Email OTP Verification")

        # 1. Try Brevo HTTP API (Port 443)
        if self.brevo_api_key:
            success, msg_id, err = await self._send_brevo_api(recipient_email, safe_name, subject, text_content, html_content)
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: Brevo, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True
            logger.warning(f"[EMAIL PROVIDER FAILED] Provider: Brevo, Recipient: {masked_dest}, Reason: {err}")

        # 2. Try Resend HTTP API (Port 443)
        if self.resend_api_key:
            success, msg_id, err = await self._send_resend_api(recipient_email, safe_name, subject, text_content, html_content)
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: Resend, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True
            logger.warning(f"[EMAIL PROVIDER FAILED] Provider: Resend, Recipient: {masked_dest}, Reason: {err}")

        # 3. Try SendGrid HTTP API (Port 443)
        if self.sendgrid_api_key:
            success, msg_id, err = await self._send_sendgrid_api(recipient_email, safe_name, subject, text_content, html_content)
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: SendGrid, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True
            logger.warning(f"[EMAIL PROVIDER FAILED] Provider: SendGrid, Recipient: {masked_dest}, Reason: {err}")

        # 4. Try Standard TLS SMTP
        if self.smtp_username and self.smtp_password:
            success, msg_id, err = await asyncio.to_thread(
                self._send_smtp_sync, recipient_email, subject, text_content, html_content
            )
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: SMTP, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True
            logger.warning(f"[EMAIL PROVIDER FAILED] Provider: SMTP, Recipient: {masked_dest}, Reason: {err}")

        # If no provider succeeded, log safe failure and return False (NEVER return True!)
        logger.error(f"[EMAIL DISPATCH FAILED] Recipient: {masked_dest}. All configured email providers failed to accept message.")
        return False




    def _build_password_reset_email_html(self, user_name: str, code: str, token: str, recipient_email: str) -> str:
        safe_name = user_name or "MindMesh User"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindMesh Password Reset</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="min-width: 100%; background-color: #0f172a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 32px 32px 24px 32px; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">MindMesh</h1>
                            <p style="margin: 4px 0 0 0; color: #e0e7ff; font-size: 13px; font-weight: 500; opacity: 0.9;">Knowledge Intelligence System</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 32px;">
                            <h2 style="margin: 0 0 12px 0; color: #f8fafc; font-size: 18px; font-weight: 600;">Password Reset Instructions</h2>
                            <p style="margin: 0 0 24px 0; color: #94a3b8; font-size: 14px; line-height: 1.6;">
                                Hello {safe_name},<br><br>
                                We received a request to reset your password for your MindMesh account (<strong>{recipient_email}</strong>). Use the verification code below to reset your password:
                            </p>
                            
                            <!-- Code Display Box -->
                            <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
                                <span style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 700; color: #818cf8; letter-spacing: 8px; display: inline-block;">{code}</span>
                            </div>

                            <p style="margin: 0 0 16px 0; color: #94a3b8; font-size: 13px; line-height: 1.6;">
                                Reset Token:<br>
                                <code style="background-color: #0f172a; border: 1px solid #334155; padding: 6px 10px; border-radius: 6px; font-size: 12px; color: #cbd5e1; word-break: break-all; display: inline-block; margin-top: 4px;">{token}</code>
                            </p>
                            
                            <p style="margin: 0 0 12px 0; color: #f59e0b; font-size: 13px; font-weight: 500; text-align: center;">
                                &#9200; This code and token expire in 24 hours.
                            </p>
                            
                            <p style="margin: 24px 0 0 0; color: #64748b; font-size: 13px; line-height: 1.5; border-top: 1px solid #334155; padding-top: 20px;">
                                If you did not request a password reset, please ignore this email.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="padding: 20px 32px; background-color: #0f172a; border-top: 1px solid #334155; text-align: center;">
                            <p style="margin: 0; color: #64748b; font-size: 12px;">Regards,<br><strong style="color: #94a3b8;">MindMesh Engineering Team</strong></p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    async def send_password_reset_email(self, recipient_email: str, user_name: str, code: str, token: str) -> bool:
        safe_name = user_name or "MindMesh User"
        subject = "MindMesh Password Reset Instructions"
        text_content = (
            f"Hello {safe_name},\n\n"
            f"Your password reset verification code is: {code}\n"
            f"Your reset token is: {token}\n\n"
            f"This code expires in 24 hours.\n"
            f"If you did not request a password reset, please ignore this email.\n\n"
            f"Regards,\nMindMesh"
        )
        html_content = self._build_password_reset_email_html(safe_name, code, token, recipient_email)
        masked_dest = mask_email(recipient_email)

        logger.info(f"[PASSWORD RESET EMAIL ATTEMPT] Recipient: {masked_dest}")

        # 1. Try Brevo HTTP API
        if self.brevo_api_key:
            success, msg_id, err = await self._send_brevo_api(recipient_email, safe_name, subject, text_content, html_content)
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: Brevo, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True

        # 2. Try Resend HTTP API
        if self.resend_api_key:
            success, msg_id, err = await self._send_resend_api(recipient_email, safe_name, subject, text_content, html_content)
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: Resend, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True

        # 3. Try SendGrid HTTP API
        if self.sendgrid_api_key:
            success, msg_id, err = await self._send_sendgrid_api(recipient_email, safe_name, subject, text_content, html_content)
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: SendGrid, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True

        # 4. Try Standard TLS SMTP
        if self.smtp_username and self.smtp_password:
            success, msg_id, err = await asyncio.to_thread(
                self._send_smtp_sync, recipient_email, subject, text_content, html_content
            )
            if success:
                logger.info(f"[EMAIL ACCEPTED] Provider: SMTP, Recipient: {masked_dest}, MessageId: {msg_id}")
                return True

        logger.error(f"[PASSWORD RESET EMAIL FAILED] Recipient: {masked_dest}. All providers failed.")
        return False


