import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

import app.models
from app.core.database import AsyncSessionLocal
from app.auth.service import AuthService
from app.auth.otp_service import OTPService
from app.auth.schemas import UserLogin, PhoneSendOtpRequest
from app.models.user import User
from app.models.otp import OtpCode
from sqlalchemy import select

async def verify_all_auth():
    async with AsyncSessionLocal() as db:
        auth_service = AuthService()
        otp_service = OTPService()
        
        print("--- 1. Testing Email & Password Auth ---")
        login_in = UserLogin(email="admin@mindmesh.com", password="adminpassword123")
        try:
            res_login = await auth_service.login(db, login_in, "Test Device", "127.0.0.1", "Test UA")
            print("[SUCCESS] Email/Password login works!")
            print("Access token generated:", res_login["access_token"][:30] + "...")
        except Exception as e:
            print("[ERROR] Email/Password login failed:", e)

        print("\n--- 2. Testing Phone OTP Generation ---")
        phone = "+919876543210"
        try:
            res_otp = await otp_service.request_phone_otp(db, phone)
            print("[SUCCESS] Mobile OTP generated successfully!")
            print("OTP response:", res_otp)
            
            # Retrieve active OTP code hash from DB
            user = (await db.execute(select(User).where(User.phone_number == phone))).scalar_one()
            otp_record = (await db.execute(
                select(OtpCode)
                .where(OtpCode.user_id == user.id, OtpCode.purpose == "phone_login", OtpCode.is_used == False)
                .order_by(OtpCode.created_at.desc())
            )).scalars().first()
            
            # Find matching code
            matched_code = None
            for candidate in range(100000, 999999):
                if otp_service.hash_otp(str(candidate)) == otp_record.otp_hash:
                    matched_code = str(candidate)
                    break
            
            print(f"\n--- 3. Testing Phone OTP Verification with matched code '{matched_code}' ---")
            ver_user, record = await otp_service.verify_phone_otp(db, phone, matched_code)
            res_session = await auth_service.create_user_session(db, ver_user, "Test Device", "127.0.0.1", "Test UA", "auth.phone_otp_login")
            print("[SUCCESS] Phone OTP login successful!")
            print("Access token generated:", res_session["access_token"][:30] + "...")
        except Exception as e:
            import traceback
            print("[ERROR] Mobile OTP workflow failed with exception:")
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_all_auth())
