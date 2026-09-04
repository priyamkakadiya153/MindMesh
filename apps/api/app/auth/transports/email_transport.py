from typing import Optional
from .base import BaseOTPTransport
from ..email_service import EmailService
from ..providers.base import EmailDeliveryResult

class EmailOTPTransport(BaseOTPTransport):
    """
    Concrete implementation of OTPTransport using EmailService and configured email providers.
    """

    def __init__(self, email_service: Optional[EmailService] = None):
        self.email_service = email_service or EmailService()
        self.last_delivery_result: Optional[EmailDeliveryResult] = None

    async def send_otp(self, recipient_identifier: str, recipient_name: str, otp_code: str) -> bool:
        """
        Delivers OTP via active email provider to user's registered email address.
        """
        result = await self.email_service.send_otp_email_detailed(
            recipient_email=recipient_identifier,
            user_name=recipient_name,
            otp_code=otp_code
        )
        self.last_delivery_result = result
        return result.success

