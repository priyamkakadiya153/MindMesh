import logging
from typing import Optional

from app.core.config import settings
from .base import BaseEmailProvider
from .brevo import BrevoEmailProvider
from .smtp import SMTPEmailProvider

logger = logging.getLogger("mindmesh.auth.email.factory")


def get_email_provider(provider_name: Optional[str] = None) -> BaseEmailProvider:
    """
    Factory resolving the active outbound email provider according to configuration:
    - Production default: 'brevo' (using Brevo HTTP REST API over Port 443)
    - Fallback / Dev: 'smtp' (using standard TLS SMTP)
    """
    selected = (provider_name or settings.EMAIL_PROVIDER or "").strip().lower()

    if selected == "brevo" or (not selected and settings.BREVO_API_KEY):
        return BrevoEmailProvider()
    elif selected == "smtp":
        return SMTPEmailProvider()
    else:
        # If Brevo API key is present, prioritize Brevo HTTP API
        if settings.BREVO_API_KEY:
            return BrevoEmailProvider()
        return SMTPEmailProvider()
