from pydantic import BaseModel, EmailStr
from typing import Optional, List, Union
from uuid import UUID
from datetime import datetime

class UserRegister(BaseModel):
    email: EmailStr
    username: Optional[str] = None
    password: Optional[str] = None
    phone_number: Optional[str] = None
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class PhoneSendOtpRequest(BaseModel):
    phone_number: str

class PhoneVerifyOtpRequest(BaseModel):
    phone_number: str
    code: str

class PhoneSendOtpResponse(BaseModel):
    status: str = "ok"
    message: str
    email_masked: str
    expires_in_seconds: int = 300
    resend_cooldown_seconds: int = 60

class RegisterSendOtpResponse(BaseModel):
    status: str = "ok"
    message: str
    email_masked: str
    registration_token: str
    expires_in_seconds: int = 300
    resend_cooldown_seconds: int = 60
    preview_otp: Optional[str] = None


class RegisterResendOtpRequest(BaseModel):
    registration_token: str

class RegisterVerifyOtpRequest(BaseModel):
    registration_token: str
    code: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class FirebaseLoginRequest(BaseModel):
    idToken: str

class SendEmailVerificationRequest(BaseModel):
    email: Optional[EmailStr] = None

class VerifyEmailRequest(BaseModel):
    token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token_or_code: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr

class ChangeMobileRequest(BaseModel):
    new_phone_number: str

class TokenRefresh(BaseModel):
    refresh_token: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    email: str
    username: str
    phone_number: Optional[str] = None
    firebase_uid: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = "UTC"
    language: Optional[str] = "en"
    theme: Optional[str] = "dark"
    is_active: bool = True
    is_verified: bool = False
    is_phone_verified: bool = False
    two_factor_enabled: bool = False
    last_login_at: Optional[datetime] = None
    current_organization_id: Optional[UUID] = None
    current_workspace_id: Optional[UUID] = None

    class Config:
        from_attributes = True

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class SessionMeta(BaseModel):
    device: str
    expires_at: datetime
    last_activity: datetime

class SessionDetailResponse(BaseModel):
    user: UserResponse
    organization: Optional[dict] = None
    workspace: Optional[dict] = None
    session: SessionMeta

class ActiveSessionResponse(BaseModel):
    id: Union[UUID, str]
    device_name: Optional[str] = None
    device: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_current: bool = False

