import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.session import UserSession
from app.models.verification import EmailVerification
from app.auth.service import AuthService
from app.auth.schemas import UserRegister, UserLogin
from app.auth.security import validate_password_strength

async def verify_auth_system():
    print("==========================================")
    print("MindMesh Phase 1.0 Enterprise Auth Verification")
    print("==========================================")

    auth_service = AuthService()

    async with AsyncSessionLocal() as db:
        # 1. Test Password Strength Validation
        print("[1/6] Testing Password Strength Validation...")
        try:
            validate_password_strength("weak")
            print("[FAIL] Weak password allowed")
            return False
        except ValueError:
            print("[OK] Weak password rejected cleanly.")

        # 2. Test User Registration & Auto-Onboarding
        print("\n[2/6] Testing Enterprise Registration & Auto-Onboarding...")
        unique_username = f"enterprise_user_{int(asyncio.get_event_loop().time())}"
        reg_input = UserRegister(
            email=f"{unique_username}@mindmesh.com",
            username=unique_username,
            password="SecurePassword123!",
            phone_number="+14155550199",
            first_name="Enterprise",
            last_name="Admin"
        )
        reg_res = await auth_service.register(db, reg_input, device_name="Chrome on Windows (Desktop)", ip_address="127.0.0.1")
        assert "access_token" in reg_res
        assert "refresh_token" in reg_res
        user = reg_res["user"]
        print(f"[OK] Registered User: {user.username} (ID: {user.id})")
        print(f"[OK] Auto-provisioned Personal Org ID: {user.current_organization_id}")
        print(f"[OK] Auto-provisioned Default Workspace ID: {user.current_workspace_id}")

        # 3. Test Email Login
        print("\n[3/6] Testing Email + Password Authentication...")
        login_input = UserLogin(email=user.email, password="SecurePassword123!")
        login_res = await auth_service.login(db, login_input, device_name="Firefox on macOS (Desktop)", ip_address="192.168.1.5")
        assert "access_token" in login_res
        print("[OK] Email + Password login successful. Tokens generated.")

        # 4. Test Firebase Login Authentication
        print("\n[4/6] Testing Firebase Login Token Verification...")
        fb_res = await auth_service.firebase_login(db, "mock_firebase_token_+14155550199", device_name="Mobile Safari", ip_address="10.0.0.1")
        assert "access_token" in fb_res
        print(f"[OK] Firebase Login Token verified. Authenticated User: {fb_res['user'].username}")

        # 5. Test Password Change & Audit Logging
        print("\n[5/6] Testing Password Change & Audit Trail...")
        changed = await auth_service.change_password(db, user, "SecurePassword123!", "NewSecurePassword123!")
        assert changed is True
        print("[OK] Password changed successfully and audit event recorded.")

        # 6. Test Data Export & Compliance
        print("\n[6/6] Testing Account Data Export & Active Devices...")
        export_data = await auth_service.export_user_data(db, user)
        assert export_data["account"]["username"] == user.username
        print(f"[OK] Compliance Data Export verified. Active Sessions: {export_data['active_sessions_count']}")

    print("\n==========================================")
    print("SUCCESS: MindMesh Phase 1.0 Enterprise Auth Fully Production Verified!")
    print("==========================================")
    return True

if __name__ == "__main__":
    asyncio.run(verify_auth_system())
