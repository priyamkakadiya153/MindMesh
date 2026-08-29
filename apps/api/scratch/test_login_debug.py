import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("."))

import app.models
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.auth.service import AuthService
from app.auth.schemas import UserLogin
from sqlalchemy import select

async def test_login():
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User))).scalars().all()
        print("Existing Users in DB:")
        for u in users:
            print(f" - ID: {u.id} | Email: {u.email} | Active: {u.is_active}")
        
        if users:
            print("\nAttempting login for 'admin@mindmesh.com' with password 'adminpassword123'...")
            req = UserLogin(email="admin@mindmesh.com", password="adminpassword123")
            auth_service = AuthService()
            try:
                res = await auth_service.login(db, req, "Test Device", "127.0.0.1", "Test UA")
                print("\n[SUCCESS] Login successful!")
                print("Access Token:", res["access_token"][:30] + "...")
                print("User Email:", res["user"].email)
            except Exception as e:
                print(f"[AUTH NOTICE] Login returned: {e}")

if __name__ == "__main__":
    asyncio.run(test_login())
