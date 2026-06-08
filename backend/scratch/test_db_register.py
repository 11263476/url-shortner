import asyncio
import sys
from sqlalchemy import select

sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.workspace import Workspace

async def test_register():
    print("[INFO] Starting database register test...")
    async with AsyncSessionLocal() as db:
        print("[INFO] Attempting to select from users table...")
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        print(f"[OK] Select completed. User exists? {user is not None}")
        
        # Now try to insert a dummy user
        import uuid
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        dummy_user = User(
            email=email,
            password_hash="hashed_pwd",
        )
        db.add(dummy_user)
        print("[INFO] Committing user...")
        await db.commit()
        await db.refresh(dummy_user)
        print(f"[OK] User committed. ID: {dummy_user.id}")
        
        # Now insert a workspace
        workspace = Workspace(
            name="Personal Workspace",
            owner_id=dummy_user.id,
        )
        db.add(workspace)
        print("[INFO] Committing workspace...")
        await db.commit()
        print("[OK] Workspace committed successfully.")

if __name__ == "__main__":
    asyncio.run(test_register())
