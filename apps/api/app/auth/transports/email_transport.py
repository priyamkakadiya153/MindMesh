from .base import BaseOTPTransport
from ..email_service import EmailService

class EmailOTPTransport(BaseOTPTransport):
    """
    Concrete implementation of OTPTransport using EmailService (SMTP).
    """

    def __init__(self, email_service: EmailService = None):
        self.email_service = email_service or EmailService()

    async def send_otp(self, recipient_identifier: str, recipient_name: str, otp_code: str) -> bool:
        """
        Delivers OTP via SMTP email to user's registered email address.
        """
        return await self.email_service.send_otp_email(
            recipient_email=recipient_identifier,
            user_name=recipient_name,
            otp_code=otp_code
        )
