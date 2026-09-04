import logging
import os
import secrets
from typing import Dict, Any, Optional
import httpx

from app.core.config import settings
from .base import BaseEmailProvider, EmailDeliveryResult

logger = logging.getLogger("mindmesh.auth.email.brevo")


def mask_email(email: str) -> str:
    """Safely masks an email address for logging (e.g., p***a@domain.com)."""
    if not email or "@" not in email:
        return "***"
    user, domain = email.split("@", 1)
    if len(user) <= 2:
        masked_user = user[0] + "***"
    else:
        masked_user = user[0] + "***" + user[-1]
    return f"{masked_user}@{domain}"


class BrevoEmailProvider(BaseEmailProvider):
    """
    Production Email Provider utilizing Brevo (Sendinblue) HTTP REST API over Port 443.
    Bypasses cloud outbound SMTP port restrictions (e.g. Render Free tier blocking ports 25, 465, 587).
    """

    BREVO_SMTP_EMAIL_URL = "https://api.brevo.com/v3/smtp/email"
    BREVO_ACCOUNT_URL = "https://api.brevo.com/v3/account"
    BREVO_SENDERS_URL = "https://api.brevo.com/v3/senders"

    def __init__(
        self,
        api_key: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ):
        raw_key = (
            api_key
            or settings.BREVO_API_KEY
            or os.environ.get("BREVO_API_KEY")
            or os.environ.get("brevo_api_key")
            or os.environ.get("SENDINBLUE_API_KEY")
            or os.environ.get("sendinblue_api_key")
            or ""
        )
        self.api_key = raw_key.strip().strip('\'"\\').strip()

        raw_from = (
            from_email
            or settings.EMAIL_FROM
            or os.environ.get("EMAIL_FROM")
            or os.environ.get("email_from")
            or settings.SMTP_FROM_EMAIL
            or settings.SMTP_USERNAME
            or ""
        )
        self.from_email = raw_from.strip().strip('\'"\\').strip()

        raw_name = (
            from_name
            or settings.EMAIL_FROM_NAME
            or os.environ.get("EMAIL_FROM_NAME")
            or settings.SMTP_FROM_NAME
            or "MindMesh"
        )
        self.from_name = raw_name.strip().strip('\'"\\').strip()

    def _build_verification_html(self, user_name: str, otp_code: str) -> str:
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
                                Your MindMesh verification code is:
                            </p>
                            
                            <!-- Code Display Box -->
                            <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
                                <span style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 700; color: #818cf8; letter-spacing: 8px; display: inline-block;">{otp_code}</span>
                            </div>
                            
                            <p style="margin: 0 0 8px 0; color: #f59e0b; font-size: 13px; font-weight: 500; text-align: center;">
                                &#9200; This code expires in 5 minutes.
                            </p>
                            <p style="margin: 0 0 16px 0; color: #ef4444; font-size: 12px; font-weight: 500; text-align: center;">
                                Do not share this code with anyone.
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

    def _build_password_reset_html(self, user_name: str, code: str, token: str, recipient_email: str) -> str:
        safe_name = user_name or "MindMesh User"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MindMesh Password Reset Instructions</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
    <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="min-width: 100%; background-color: #0f172a; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table role="presentation" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 520px; background-color: #1e293b; border: 1px solid #334155; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);">
                    <tr>
                        <td style="padding: 32px 32px 24px 32px; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px; font-weight: 700; letter-spacing: -0.5px;">MindMesh</h1>
                            <p style="margin: 4px 0 0 0; color: #e0e7ff; font-size: 13px; font-weight: 500; opacity: 0.9;">Knowledge Intelligence System</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 32px;">
                            <h2 style="margin: 0 0 12px 0; color: #f8fafc; font-size: 18px; font-weight: 600;">Password Reset Instructions</h2>
                            <p style="margin: 0 0 24px 0; color: #94a3b8; font-size: 14px; line-height: 1.6;">
                                Hello {safe_name},<br><br>
                                Use the verification code below to reset your MindMesh account password:
                            </p>
                            <div style="background-color: #0f172a; border: 1px solid #475569; border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 24px;">
                                <span style="font-family: 'Courier New', Courier, monospace; font-size: 36px; font-weight: 700; color: #818cf8; letter-spacing: 8px; display: inline-block;">{code}</span>
                            </div>
                            <p style="margin: 0 0 12px 0; color: #f59e0b; font-size: 13px; font-weight: 500; text-align: center;">
                                &#9200; This code expires in 24 hours.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>"""

    async def send_verification_email(
        self,
        recipient_email: str,
        recipient_name: str,
        otp_code: str
    ) -> EmailDeliveryResult:
        """
        Calls Brevo HTTP API to send transactional verification email.
        """
        masked_dest = mask_email(recipient_email)
        key_present = bool(self.api_key)
        key_prefix = "xkeysib-" if self.api_key.startswith("xkeysib-") else ("none" if not self.api_key else "other")
        key_len = len(self.api_key)

        logger.info(
            "provider=brevo recipient=%s action=send_verification brevo_key_present=%s brevo_key_prefix=%s key_length=%s",
            masked_dest, key_present, key_prefix, key_len
        )

        # 1. Validate API Key presence
        if not self.api_key:
            logger.error(
                "provider=brevo recipient=%s status=failed error_category=missing_api_key brevo_key_present=false brevo_key_prefix=none key_length=0",
                masked_dest
            )
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category="missing_api_key",
                error_message="BREVO_API_KEY environment variable is not configured in Render."
            )

        # 2. Validate Sender Configuration
        if not self.from_email:
            logger.error(
                "provider=brevo recipient=%s status=failed error_category=missing_sender brevo_key_present=%s brevo_key_prefix=%s key_length=%s",
                masked_dest, key_present, key_prefix, key_len
            )
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category="missing_sender",
                error_message="EMAIL_FROM environment variable is not configured in Render (must be verified sender in Brevo)."
            )

        subject = "Verify your MindMesh email"
        safe_name = recipient_name or "MindMesh User"
        text_content = (
            f"Hello {safe_name},\n\n"
            f"Your MindMesh verification code is: {otp_code}\n\n"
            f"This code expires in 5 minutes.\n"
            f"Do not share this code with anyone.\n\n"
            f"If you did not request this verification code, please ignore this email.\n\n"
            f"Regards,\nMindMesh Security Team"
        )
        html_content = self._build_verification_html(safe_name, otp_code)

        payload = {
            "sender": {
                "name": self.from_name,
                "email": self.from_email
            },
            "to": [
                {
                    "email": recipient_email,
                    "name": safe_name
                }
            ],
            "subject": subject,
            "htmlContent": html_content,
            "textContent": text_content
        }

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(self.BREVO_SMTP_EMAIL_URL, headers=headers, json=payload)

            if resp.status_code in (200, 201):
                try:
                    data = resp.json()
                    msg_id = data.get("messageId", f"brevo_{secrets.token_hex(4)}")
                except Exception:
                    msg_id = f"brevo_{secrets.token_hex(4)}"

                logger.info(
                    "provider=brevo recipient=%s status=accepted message_id=%s brevo_key_present=true brevo_key_prefix=%s key_length=%s",
                    masked_dest, msg_id, key_prefix, key_len
                )
                return EmailDeliveryResult(
                    success=True,
                    provider="brevo",
                    message_id=msg_id
                )

            # Analyze HTTP error response
            status_code = resp.status_code
            error_body = resp.text

            if status_code == 401:
                category = "invalid_api_key"
                err_msg = "Invalid Brevo API key (HTTP 401 Unauthorized - Key not found)."
            elif status_code == 403:
                category = "unauthorized_or_forbidden"
                err_msg = "Brevo account access forbidden (HTTP 403 Forbidden)."
            elif status_code == 400 and any(kw in error_body.lower() for kw in ["sender", "verified", "authorized"]):
                category = "unverified_sender"
                err_msg = f"Sender email '{mask_email(self.from_email)}' is not registered or verified on Brevo."
            elif status_code == 429:
                category = "rate_limited"
                err_msg = "Brevo account rate limit exceeded. Please try again later."
            else:
                category = "brevo_api_error"
                err_msg = f"Brevo HTTP error (status {status_code})."

            logger.error(
                "provider=brevo recipient=%s status=failed error_category=%s status_code=%s brevo_key_present=true brevo_key_prefix=%s key_length=%s",
                masked_dest, category, status_code, key_prefix, key_len
            )
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category=category,
                error_message=err_msg
            )

        except (httpx.ConnectTimeout, httpx.ReadTimeout, TimeoutError) as timeout_err:
            logger.error(
                "provider=brevo recipient=%s status=failed error_category=network_timeout brevo_key_present=%s brevo_key_prefix=%s key_length=%s",
                masked_dest, key_present, key_prefix, key_len
            )
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category="network_timeout",
                error_message="Network timeout connecting to Brevo HTTP API."
            )
        except Exception as e:
            logger.error(
                "provider=brevo recipient=%s status=failed error_category=network_error error=%s brevo_key_present=%s brevo_key_prefix=%s key_length=%s",
                masked_dest, str(e), key_present, key_prefix, key_len
            )
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category="network_error",
                error_message=f"Failed to deliver email through Brevo: {str(e)}"
            )

    async def send_password_reset_email(
        self,
        recipient_email: str,
        recipient_name: str,
        code: str,
        token: str
    ) -> EmailDeliveryResult:
        """Calls Brevo HTTP API to send password reset code."""
        masked_dest = mask_email(recipient_email)
        if not self.api_key or not self.from_email:
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category="configuration_error",
                error_message="Brevo credentials or sender email not configured."
            )

        subject = "MindMesh Password Reset Instructions"
        safe_name = recipient_name or "MindMesh User"
        text_content = (
            f"Hello {safe_name},\n\n"
            f"Your password reset verification code is: {code}\n\n"
            f"This code expires in 24 hours.\n"
            f"If you did not request a password reset, please ignore this email.\n\n"
            f"Regards,\nMindMesh Security Team"
        )
        html_content = self._build_password_reset_html(safe_name, code, token, recipient_email)

        payload = {
            "sender": {"name": self.from_name, "email": self.from_email},
            "to": [{"email": recipient_email, "name": safe_name}],
            "subject": subject,
            "htmlContent": html_content,
            "textContent": text_content
        }

        headers = {
            "api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(self.BREVO_SMTP_EMAIL_URL, headers=headers, json=payload)
            if resp.status_code in (200, 201):
                return EmailDeliveryResult(success=True, provider="brevo", message_id=resp.json().get("messageId"))
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category="brevo_api_error",
                error_message=f"Brevo HTTP error {resp.status_code}"
            )
        except Exception as e:
            return EmailDeliveryResult(
                success=False,
                provider="brevo",
                error_category="network_error",
                error_message=str(e)
            )

    async def verify_account_status(self) -> Dict[str, Any]:
        """
        Diagnostic: Calls GET https://api.brevo.com/v3/account with api-key: BREVO_API_KEY.
        Safe: Returns HTTP status and account metadata without exposing raw secrets.
        """
        key_present = bool(self.api_key)
        key_prefix = "xkeysib-" if self.api_key.startswith("xkeysib-") else ("none" if not self.api_key else "other")
        key_len = len(self.api_key)

        if not self.api_key:
            return {
                "http_status": None,
                "key_accepted": False,
                "brevo_key_present": False,
                "brevo_key_prefix": "none",
                "key_length": 0,
                "error_category": "missing_api_key",
                "message": "BREVO_API_KEY is not configured in Render environment."
            }

        headers = {
            "api-key": self.api_key,
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.BREVO_ACCOUNT_URL, headers=headers)

            status_code = resp.status_code
            if status_code == 200:
                data = resp.json()
                acc_email = data.get("email", "")
                company = data.get("companyName", "")
                plans = [p.get("type") for p in data.get("plan", []) if isinstance(p, dict)]
                logger.info(
                    "provider=brevo action=verify_account status=accepted http_code=200 brevo_key_present=true brevo_key_prefix=%s key_length=%s",
                    key_prefix, key_len
                )
                return {
                    "http_status": 200,
                    "key_accepted": True,
                    "brevo_key_present": True,
                    "brevo_key_prefix": key_prefix,
                    "key_length": key_len,
                    "account_email_masked": mask_email(acc_email),
                    "company_name": company,
                    "plans": plans,
                    "message": "Brevo API key is valid and accepted (HTTP 200 OK)."
                }
            elif status_code in (401, 403):
                category = "invalid_api_key" if status_code == 401 else "unauthorized_or_forbidden"
                logger.error(
                    "provider=brevo action=verify_account status=rejected http_code=%s brevo_key_present=true brevo_key_prefix=%s key_length=%s",
                    status_code, key_prefix, key_len
                )
                return {
                    "http_status": status_code,
                    "key_accepted": False,
                    "brevo_key_present": True,
                    "brevo_key_prefix": key_prefix,
                    "key_length": key_len,
                    "error_category": category,
                    "message": f"Brevo rejected API key with HTTP {status_code} ({resp.text[:200]})."
                }
            else:
                logger.error(
                    "provider=brevo action=verify_account status=error http_code=%s brevo_key_present=true brevo_key_prefix=%s key_length=%s",
                    status_code, key_prefix, key_len
                )
                return {
                    "http_status": status_code,
                    "key_accepted": False,
                    "brevo_key_present": True,
                    "brevo_key_prefix": key_prefix,
                    "key_length": key_len,
                    "error_category": "brevo_api_error",
                    "message": f"Brevo account endpoint returned HTTP {status_code}: {resp.text[:200]}"
                }
        except Exception as e:
            logger.error(
                "provider=brevo action=verify_account status=failed error_category=network_error error=%s",
                str(e)
            )
            return {
                "http_status": None,
                "key_accepted": False,
                "brevo_key_present": True,
                "brevo_key_prefix": key_prefix,
                "key_length": key_len,
                "error_category": "network_error",
                "message": f"Network error connecting to Brevo: {str(e)}"
            }

    async def verify_sender_status(self) -> Dict[str, Any]:
        """
        Diagnostic method: Queries Brevo API for registered & active senders.
        Verifies if the configured EMAIL_FROM is an authorized sender on Brevo.
        """
        if not self.api_key:
            return {
                "configured": False,
                "is_sender_verified": False,
                "error": "BREVO_API_KEY is not set."
            }

        headers = {
            "api-key": self.api_key,
            "Accept": "application/json"
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(self.BREVO_SENDERS_URL, headers=headers)

            if resp.status_code == 401:
                return {
                    "valid_key": False,
                    "is_sender_verified": False,
                    "error": "Brevo API key is unauthorized / invalid (HTTP 401)."
                }
            if resp.status_code != 200:
                return {
                    "valid_key": False,
                    "is_sender_verified": False,
                    "error": f"Brevo senders check returned HTTP {resp.status_code}: {resp.text[:200]}"
                }

            senders_data = resp.json().get("senders", [])
            verified_emails = [s.get("email") for s in senders_data if s.get("active")]
            configured_sender = self.from_email.lower()
            is_verified = any(e and e.lower() == configured_sender for e in verified_emails)

            return {
                "valid_key": True,
                "configured_sender": mask_email(self.from_email),
                "is_sender_verified": is_verified,
                "active_senders_count": len(verified_emails),
                "verified_senders_masked": [mask_email(e) for e in verified_emails if e]
            }
        except Exception as e:
            return {
                "valid_key": False,
                "is_sender_verified": False,
                "error": f"Failed to connect to Brevo API: {str(e)}"
            }
