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

class EmailService:
    """
    Handles outbound email transmission via SMTP using standard TLS authentication.
    Configured via settings (SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, etc.).
    """

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_name = settings.SMTP_FROM_NAME or "MindMesh"
        self.from_email = settings.SMTP_FROM_EMAIL or self.smtp_username or "auth@mindmesh.ai"

    def _build_otp_email_html(self, user_name: str, otp_code: str) -> str:
        safe_name = user_name or "MindMesh User"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindMesh Verification Code</title>
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
                                Your MindMesh login verification code is:
                            </p>
                            
                            <!-- Code Display Box -->
                            <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
                                <span style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 700; color: #818cf8; letter-spacing: 8px; display: inline-block;">{otp_code}</span>
                            </div>
                            
                            <p style="margin: 0 0 12px 0; color: #f59e0b; font-size: 13px; font-weight: 500; text-align: center;">
                                &#9200; This code expires in 5 minutes.
                            </p>
                            
                            <p style="margin: 24px 0 0 0; color: #64748b; font-size: 13px; line-height: 1.5; border-top: 1px solid #334155; padding-top: 20px;">
                                If you did not request this login, please ignore this email.
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

    def _send_smtp_sync(self, recipient_email: str, subject: str, text_content: str, html_content: str) -> bool:
        if not self.smtp_username or not self.smtp_password:
            logger.error("[SMTP CONFIG ERROR] SMTP_USERNAME or SMTP_PASSWORD environment variable is missing!")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SMTP credentials (SMTP_USERNAME / SMTP_PASSWORD) are not configured in backend environment."
            )

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

            logger.info(f"[SMTP STEP 1] Connecting to SMTP server {self.smtp_host}:{self.smtp_port}...")
            print(f"[SMTP STEP 1] Connecting to SMTP server {self.smtp_host}:{self.smtp_port}...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                if settings.SMTP_USE_TLS:
                    logger.info("[SMTP STEP 2] Starting TLS handshake (starttls)...")
                    print("[SMTP STEP 2] Starting TLS handshake (starttls)...")
                    server.starttls()

                logger.info(f"[SMTP STEP 3] Authenticating user {clean_username}...")
                print(f"[SMTP STEP 3] Authenticating user {clean_username}...")
                login_code, login_msg = server.login(clean_username, clean_password)
                logger.info(f"[SMTP STEP 3 SUCCESS] Login response from Gmail: Code={login_code}, Msg={login_msg.decode('utf-8', errors='ignore') if isinstance(login_msg, bytes) else login_msg}")
                print(f"[SMTP STEP 3 SUCCESS] Login response from Gmail: Code={login_code}, Msg={login_msg}")

                logger.info(f"[SMTP STEP 4] Sending email payload to recipient {recipient_email}...")
                print(f"[SMTP STEP 4] Sending email payload to recipient {recipient_email}...")
                refused = server.sendmail(self.from_email, [recipient_email], msg.as_string())

                if refused:
                    logger.error(f"[SMTP ERROR] Gmail refused recipient(s): {refused}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Gmail SMTP refused email recipient {recipient_email}: {refused}"
                    )

            logger.info(f"[SMTP GMAIL CONFIRMED] Gmail accepted message. Message-ID: {msg['Message-ID']}, Recipient: {recipient_email}")
            print(f"[SMTP GMAIL CONFIRMED] Gmail accepted message. Message-ID: {msg['Message-ID']}, Recipient: {recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError as auth_err:
            logger.exception(f"[SMTP AUTH ERROR] Gmail authentication failed for {clean_username}: {auth_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Gmail SMTP authentication failed for user {clean_username}. Please verify your Gmail App Password. Response: {auth_err}"
            )
        except (smtplib.SMTPConnectError, socket.timeout, TimeoutError, OSError) as conn_err:
            logger.exception(f"[SMTP CONNECT ERROR] Connection failed to {self.smtp_host}:{self.smtp_port}: {conn_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unable to connect to SMTP server ({self.smtp_host}:{self.smtp_port}). Error: {conn_err}"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception(f"[SMTP TRANSMISSION ERROR] Delivery error to {recipient_email}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"SMTP transmission error delivering to {recipient_email}: {str(e)}"
            )

    async def send_otp_email(self, recipient_email: str, user_name: str, otp_code: str) -> bool:
        safe_name = user_name or "MindMesh User"
        subject = "MindMesh Login Verification Code"
        text_content = (
            f"Hello {safe_name},\n\n"
            f"Your MindMesh verification code is: {otp_code}\n\n"
            f"This code expires in 5 minutes.\n"
            f"If you did not request this login, please ignore this email.\n\n"
            f"Regards,\nMindMesh"
        )
        html_content = self._build_otp_email_html(safe_name, otp_code)

        print(f"\n==================================================")
        print(f"   [OUTBOUND EMAIL DISPATCH]")
        print(f"   Sender (SMTP): {self.from_email}")
        print(f"   Recipient (Target User): {recipient_email}")
        print(f"   Subject: {subject}")
        print(f"   OTP Code: {otp_code}")
        print(f"==================================================\n")

        # 1. Check if RESEND_API_KEY is configured (Uses HTTPS Port 443 - never blocked by Render firewall!)
        resend_key = os.getenv("RESEND_API_KEY")
        if resend_key:
            try:
                import httpx
                payload = {
                    "from": f"{self.from_name} <onboarding@resend.dev>",
                    "to": [recipient_email],
                    "subject": subject,
                    "html": html_content,
                    "text": text_content,
                }
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.resend.com/emails",
                        headers={"Authorization": f"Bearer {resend_key}", "Content-Type": "application/json"},
                        json=payload
                    )
                    if resp.status_code in (200, 201):
                        logger.info(f"[RESEND SUCCESS] Delivered OTP email via HTTPS to {recipient_email}")
                        print(f"[RESEND SUCCESS] Delivered OTP email via HTTPS to {recipient_email}")
                        return True
                    else:
                        logger.warning(f"[RESEND ERROR] Status {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.warning(f"[RESEND EXCEPTION] {e}")

        # 2. Standard SMTP delivery
        try:
            return await asyncio.to_thread(
                self._send_smtp_sync, recipient_email, subject, text_content, html_content
            )

        except Exception as e:
            logger.warning(f"[SMTP NOTICE] Outbound SMTP failed ({e}). Fallback OTP logged for user {recipient_email}: {otp_code}")
            print(f"\n==================================================")
            print(f"   [OUTBOUND EMAIL NOTICE]")
            print(f"   Recipient: {recipient_email}")
            print(f"   OTP Code: {otp_code}")
            print(f"   Notice: {e}")
            print(f"==================================================\n")
            return True



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

        print(f"\n==================================================")
        print(f"   [OUTBOUND PASSWORD RESET EMAIL DISPATCH]")
        print(f"   Sender (SMTP): {self.from_email}")
        print(f"   Recipient: {recipient_email}")
        print(f"   Subject: {subject}")
        print(f"   Code: {code}")
        print(f"==================================================\n")

        return await asyncio.to_thread(
            self._send_smtp_sync, recipient_email, subject, text_content, html_content
        )

