from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseOTPTransport(ABC):
    """
    Abstract Base Class defining the OTP Delivery Transport interface.
    This enables pluggable delivery mechanisms (e.g. Email, SMS, WhatsApp)
    without mutating authentication flow, state machines, or business logic.
    """

    @abstractmethod
    async def send_otp(self, recipient_identifier: str, recipient_name: str, otp_code: str) -> bool:
        """
        Delivers the OTP to the specified target recipient.
        :param recipient_identifier: Email address, Phone number, or Target ID depending on transport
        :param recipient_name: Display name of the recipient
        :param otp_code: Plain 6-digit verification OTP code
        :return: Boolean indicating transmission success
        """
        pass
