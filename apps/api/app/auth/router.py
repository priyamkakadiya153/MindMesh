from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from ..core.database import get_db_session
from .service import AuthService
from .otp_service import OTPService
from .schemas import (
    UserRegister, UserLogin, FirebaseLoginRequest, TokenRefresh, TokenResponse, UserResponse, AuthResponse,
    ActiveSessionResponse, SessionDetailResponse, SessionMeta,
    SendEmailVerificationRequest, VerifyEmailRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    PhoneSendOtpRequest, PhoneVerifyOtpRequest, PhoneSendOtpResponse,
    RegisterSendOtpResponse, RegisterResendOtpRequest, RegisterVerifyOtpRequest
)
from .dependencies import get_current_user
from ..models.user import User
from ..models.session import UserSession
from ..models.organization import Organization
from ..workspace.models import Workspace
from ..core.config import settings

router = APIRouter()
auth_service = AuthService()
otp_service = OTPService()

def get_request_metadata(request: Request):
    user_agent = request.headers.get("user-agent", "")
    ip_address = request.client.host if request.client else "Unknown"
    
    device_type = "Desktop"
    if "Mobi" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        device_type = "Mobile"
    elif "iPad" in user_agent or "Tablet" in user_agent:
        device_type = "Tablet"
        
    os_name = "Unknown OS"
    if "Windows" in user_agent:
        os_name = "Windows"
    elif "Macintosh" in user_agent or "Mac OS X" in user_agent:
        os_name = "macOS"
    elif "Linux" in user_agent:
        if "Android" in user_agent:
            os_name = "Android"
        else:
            os_name = "Linux"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        os_name = "iOS"
        
    browser_name = "Unknown Browser"
    if "Firefox" in user_agent:
        browser_name = "Firefox"
    elif "Chrome" in user_agent and "Safari" in user_agent and "Edg" not in user_agent:
        browser_name = "Chrome"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        browser_name = "Safari"
    elif "Edg" in user_agent:
        browser_name = "Edge"
        
    device_name = f"{browser_name} on {os_name} ({device_type})"
    return device_name, ip_address, user_agent

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    is_prod = (settings.NODE_ENV == "production")
    samesite_val = "none" if is_prod else "lax"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite=samesite_val,
        secure=is_prod,
        max_age=15 * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite=samesite_val,
        secure=is_prod,
        max_age=30 * 24 * 60 * 60,
    )

def clear_auth_cookies(response: Response):
    is_prod = (settings.NODE_ENV == "production")
    samesite_val = "none" if is_prod else "lax"
    response.delete_cookie(key="access_token", httponly=True, samesite=samesite_val, secure=is_prod)
    response.delete_cookie(key="refresh_token", httponly=True, samesite=samesite_val, secure=is_prod)


@router.post("/register", response_model=RegisterSendOtpResponse)
async def register(request: Request, user_in: UserRegister, db: AsyncSession = Depends(get_db_session)):
    return await auth_service.initiate_registration(db, user_in)

@router.post("/register/resend-otp", response_model=RegisterSendOtpResponse)
async def resend_registration_otp(request: Request, req: RegisterResendOtpRequest, db: AsyncSession = Depends(get_db_session)):
    return await auth_service.resend_registration_otp(db, req.registration_token)

@router.post("/register/verify-otp", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def verify_registration_otp(request: Request, response: Response, req: RegisterVerifyOtpRequest, db: AsyncSession = Depends(get_db_session)):
    device_name, ip_address, user_agent = get_request_metadata(request)
    res = await auth_service.complete_registration(db, req.registration_token, req.code, device_name, ip_address, user_agent)
    set_auth_cookies(response, res["access_token"], res["refresh_token"])
    return {
        "access_token": res["access_token"],
        "refresh_token": res["refresh_token"],
        "token_type": res["token_type"],
        "user": res["user"]
    }

@router.post("/login", response_model=AuthResponse)
async def login(request: Request, response: Response, login_in: UserLogin, db: AsyncSession = Depends(get_db_session)):
    device_name, ip_address, user_agent = get_request_metadata(request)
    res = await auth_service.login(db, login_in, device_name, ip_address, user_agent)
    set_auth_cookies(response, res["access_token"], res["refresh_token"])
    return {
        "access_token": res["access_token"],
        "refresh_token": res["refresh_token"],
        "token_type": res["token_type"],
        "user": res["user"]
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, refresh_in: Optional[TokenRefresh] = None, db: AsyncSession = Depends(get_db_session)):
    token = None
    if refresh_in and refresh_in.refresh_token:
        token = refresh_in.refresh_token
    if not token:
        token = request.cookies.get("refresh_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please sign in again."
        )

    device_name, ip_address, user_agent = get_request_metadata(request)
    res = await auth_service.refresh_tokens(db, token, device_name, ip_address, user_agent)
    set_auth_cookies(response, res["access_token"], res["refresh_token"])
    return res

@router.post("/logout")
async def logout(request: Request, response: Response, refresh_in: Optional[TokenRefresh] = None, db: AsyncSession = Depends(get_db_session)):
    token = None
    if refresh_in and refresh_in.refresh_token:
        token = refresh_in.refresh_token
    if not token:
        token = request.cookies.get("refresh_token")

    if token:
        await auth_service.logout(db, token)
        
    clear_auth_cookies(response)
    return {"status": "ok", "message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/session", response_model=SessionDetailResponse)
async def get_session(request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    session_id = request.state.session_id if hasattr(request.state, "session_id") else None
    if not session_id:
        raise HTTPException(status_code=401, detail="Session not identified")
        
    db_session = await auth_service.repo.get_session_by_id(db, session_id)
    if not db_session:
        raise HTTPException(status_code=401, detail="Session not found")
        
    org = None
    if current_user.current_organization_id:
        org_stmt = select(Organization).where(Organization.id == current_user.current_organization_id)
        org_res = await db.execute(org_stmt)
        org_obj = org_res.scalar_one_or_none()
        if org_obj:
            org = {"id": str(org_obj.id), "name": org_obj.name, "slug": org_obj.slug}
            
    workspace = None
    if current_user.current_workspace_id:
        ws_stmt = select(Workspace).where(Workspace.id == current_user.current_workspace_id)
        ws_res = await db.execute(ws_stmt)
        ws_obj = ws_res.scalar_one_or_none()
        if ws_obj:
            workspace = {"id": str(ws_obj.id), "name": ws_obj.name, "slug": ws_obj.slug}
            
    device_type, browser, os = get_request_metadata(request)
    
    return SessionDetailResponse(
        user=UserResponse.from_orm(current_user),
        organization=org,
        workspace=workspace,
        session=SessionMeta(
            device=f"{browser} on {os} ({device_type})" if browser != "Unknown Browser" else db_session.device_name or "Unknown Device",
            expires_at=db_session.expires_at,
            last_activity=db_session.updated_at
        )
    )

@router.get("/sessions", response_model=List[ActiveSessionResponse])
async def get_sessions(request: Request, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    current_session_id = request.state.session_id if hasattr(request.state, "session_id") else None
    db_sessions = await auth_service.repo.list_active_sessions(db, current_user.id)
    
    sessions_list = []
    for s in db_sessions:
        sessions_list.append(
            ActiveSessionResponse(
                id=s.id,
                device=s.device_name or "Unknown Device",
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                created_at=s.created_at,
                last_activity=s.updated_at,
                expires_at=s.expires_at,
                is_current=(s.id == current_session_id)
            )
        )
    return sessions_list

@router.delete("/sessions/{session_id}")
async def revoke_session(session_id: UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    db_session = await auth_service.repo.get_session_by_id(db, session_id)
    if not db_session or db_session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db_session.revoked = True
    db_session.updated_at = datetime.utcnow()
    db.add(db_session)
    await db.commit()
    return {"status": "ok", "message": "Session revoked"}

@router.post("/logout-all")
async def logout_all(response: Response, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    await auth_service.logout_all(db, current_user.id)
    clear_auth_cookies(response)
    return {"status": "ok", "message": "Logged out from all devices"}

# --- Firebase Authentication Endpoint ---

@router.post("/firebase-login", response_model=AuthResponse)
async def firebase_login(request: Request, response: Response, body: FirebaseLoginRequest, db: AsyncSession = Depends(get_db_session)):
    device_name, ip_address, user_agent = get_request_metadata(request)
    res = await auth_service.firebase_login(db, body.idToken, device_name, ip_address, user_agent)
    set_auth_cookies(response, res["access_token"], res["refresh_token"])
    return {
        "access_token": res["access_token"],
        "refresh_token": res["refresh_token"],
        "token_type": res["token_type"],
        "user": res["user"]
    }

# --- Email & Password Recovery Endpoints ---

@router.post("/email/send-verification")
async def send_email_verification(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db_session)):
    token, _ = await auth_service.email_service.send_email_verification(db, current_user)
    return {"status": "ok", "message": "Verification email sent.", "dev_token": token}

@router.post("/email/verify")
async def verify_email(body: VerifyEmailRequest, db: AsyncSession = Depends(get_db_session)):
    user = await auth_service.email_service.verify_email_token(db, body.token)
    return {"status": "ok", "message": "Email verified successfully.", "user_id": str(user.id)}

@router.post("/password/forgot")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db_session)):
    await auth_service.request_password_reset(db, body.email)
    return {"status": "ok", "message": "If account exists, password reset instructions have been sent."}

@router.post("/password/reset")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db_session)):
    await auth_service.reset_password(db, body.token_or_code, body.new_password)
    return {"status": "ok", "message": "Password reset successfully. Please sign in with your new password."}

# --- Phone Number + Email OTP Endpoints ---

@router.post("/phone/send-otp", response_model=PhoneSendOtpResponse)
async def send_phone_otp(body: PhoneSendOtpRequest, db: AsyncSession = Depends(get_db_session)):
    return await otp_service.request_phone_otp(db, body.phone_number)

@router.post("/phone/resend-otp", response_model=PhoneSendOtpResponse)
async def resend_phone_otp(body: PhoneSendOtpRequest, db: AsyncSession = Depends(get_db_session)):
    return await otp_service.request_phone_otp(db, body.phone_number)

@router.post("/phone/verify-otp", response_model=AuthResponse)
async def verify_phone_otp(request: Request, response: Response, body: PhoneVerifyOtpRequest, db: AsyncSession = Depends(get_db_session)):
    user, otp_record = await otp_service.verify_phone_otp(db, body.phone_number, body.code)
    device_name, ip_address, user_agent = get_request_metadata(request)
    res = await auth_service.create_user_session(db, user, device_name, ip_address, user_agent, "auth.phone_otp_login")
    set_auth_cookies(response, res["access_token"], res["refresh_token"])
    return {
        "access_token": res["access_token"],
        "refresh_token": res["refresh_token"],
        "token_type": res["token_type"],
        "user": res["user"]
    }

