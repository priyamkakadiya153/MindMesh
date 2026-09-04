from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel


class EmailDeliveryResult(BaseModel):
    success: bool
    provider: str
    message_id: Optional[str] = None
    error_category: Optional[str] = None  # "unverified_sender", "invalid_api_key", "rate_limited", "network_error", etc.
    error_message: Optional[str] = None


class BaseEmailProvider(ABC):
    """
    Abstract Base Class for MindMesh Outbound Email Providers.
    """

    @abstractmethod
    async def send_verification_email(
        self,
        recipient_email: str,
        recipient_name: str,
        otp_code: str
    ) -> EmailDeliveryResult:
        """Dispatches an email verification OTP to the target recipient."""
        pass

    @abstractmethod
    async def send_password_reset_email(
        self,
        recipient_email: str,
        recipient_name: str,
        code: str,
        token: str
    ) -> EmailDeliveryResult:
        """Dispatches a password reset code/token email to the target recipient."""
        pass

    @abstractmethod
    async def verify_sender_status(self) -> Dict[str, Any]:
        """Validates provider credentials and checks whether the configured sender is authorized."""
        pass
