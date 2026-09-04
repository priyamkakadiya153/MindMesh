import asyncio
import logging
import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Dict, Any, Optional

from app.core.config import settings
from .base import BaseEmailProvider, EmailDeliveryResult
from .brevo import mask_email

logger = logging.getLogger("mindmesh.auth.email.smtp")


class SMTPEmailProvider(BaseEmailProvider):
    """
    Standard TLS SMTP Email Provider (used in local development or self-hosted SMTP environments).
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: Optional[bool] = None
    ):
        self.host = host or settings.SMTP_HOST
        self.port = port or settings.SMTP_PORT
        self.username = (username or settings.SMTP_USERNAME or "").strip()
        self.password = (password or settings.SMTP_PASSWORD or "").replace(" ", "")
        self.from_email = (from_email or settings.EMAIL_FROM or settings.SMTP_FROM_EMAIL or self.username or "auth@mindmesh.ai").strip()
        self.from_name = (from_name or settings.EMAIL_FROM_NAME or settings.SMTP_FROM_NAME or "MindMesh").strip()
        self.use_tls = use_tls if use_tls is not None else settings.SMTP_USE_TLS

    def _send_sync(self, recipient_email: str, subject: str, text_content: str, html_content: str) -> EmailDeliveryResult:
        if not self.username or not self.password:
            return EmailDeliveryResult(
                success=False,
                provider="smtp",
                error_category="missing_credentials",
                error_message="SMTP username or password not configured."
            )

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = recipient_email
            msg["Date"] = formatdate(localtime=True)
            msg_id = make_msgid(domain="mindmesh.ai")
            msg["Message-ID"] = msg_id

            msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP(self.host, self.port, timeout=12) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                refused = server.sendmail(self.from_email, [recipient_email], msg.as_string())
                if refused:
                    return EmailDeliveryResult(
                        success=False,
                        provider="smtp",
                        error_category="recipient_refused",
                        error_message=f"SMTP server refused recipient: {refused}"
                    )

            logger.info("provider=smtp recipient=%s status=accepted message_id=%s", mask_email(recipient_email), msg_id)
            return EmailDeliveryResult(success=True, provider="smtp", message_id=msg_id)

        except smtplib.SMTPAuthenticationError as auth_err:
            logger.error("provider=smtp recipient=%s status=failed error_category=auth_error", mask_email(recipient_email))
            return EmailDeliveryResult(success=False, provider="smtp", error_category="auth_error", error_message=str(auth_err))
        except (smtplib.SMTPConnectError, socket.timeout, TimeoutError, OSError) as conn_err:
            logger.error("provider=smtp recipient=%s status=failed error_category=network_error", mask_email(recipient_email))
            return EmailDeliveryResult(success=False, provider="smtp", error_category="network_error", error_message=str(conn_err))
        except Exception as e:
            logger.error("provider=smtp recipient=%s status=failed error_category=unexpected_error", mask_email(recipient_email))
            return EmailDeliveryResult(success=False, provider="smtp", error_category="unexpected_error", error_message=str(e))

    async def send_verification_email(
        self,
        recipient_email: str,
        recipient_name: str,
        otp_code: str
    ) -> EmailDeliveryResult:
        safe_name = recipient_name or "MindMesh User"
        subject = "Verify your MindMesh email"
        text_content = (
            f"Hello {safe_name},\n\n"
            f"Your MindMesh verification code is: {otp_code}\n\n"
            f"This code expires in 5 minutes.\n"
            f"Do not share this code with anyone.\n\n"
            f"If you did not request this verification code, please ignore this email.\n\n"
            f"Regards,\nMindMesh Security Team"
        )
        html_content = f"<h3>Hello {safe_name},</h3><p>Your MindMesh verification code is: <b>{otp_code}</b></p><p>This code expires in 5 minutes. Do not share this code with anyone.</p>"

        return await asyncio.to_thread(
            self._send_sync, recipient_email, subject, text_content, html_content
        )

    async def send_password_reset_email(
        self,
        recipient_email: str,
        recipient_name: str,
        code: str,
        token: str
    ) -> EmailDeliveryResult:
        safe_name = recipient_name or "MindMesh User"
        subject = "MindMesh Password Reset Instructions"
        text_content = f"Hello {safe_name},\n\nYour password reset code is: {code}\nReset token: {token}\nExpires in 24 hours."
        html_content = f"<p>Hello {safe_name},</p><p>Your password reset code is: <b>{code}</b></p><p>Token: {token}</p>"

        return await asyncio.to_thread(
            self._send_sync, recipient_email, subject, text_content, html_content
        )

    async def verify_sender_status(self) -> Dict[str, Any]:
        return {
            "valid_key": bool(self.username and self.password),
            "configured_sender": self.from_email,
            "provider": "smtp"
        }
