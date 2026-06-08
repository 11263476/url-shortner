import sys
import time
import asyncio
import httpx
from sqlalchemy import select, delete

# Add backend/src to path
sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.main import app
from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.workspace import Workspace
from src.models.url import URL
from src.core.redis import redis_client

async def run_integration_tests():
    # 1. Unique email for registration
    ts = int(time.time())
    email = f"test_user_{ts}@example.com"
    password = "testpassword123"
    
    # Use ASGITransport for newer versions of httpx
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print(f"1. Registering user: {email}...")
        reg_response = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
        assert reg_response.status_code == 201
        user_id = reg_response.json()["id"]
        print(f"   [SUCCESS] Registered user with ID: {user_id}")
        
        print("2. Logging in...")
        login_response = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        headers = {"Authorization": f"Bearer {access_token}"}
        print("   [SUCCESS] Login successful")

        # Fetch default workspace ID
        async with AsyncSessionLocal() as db:
            res = await db.execute(select(Workspace).where(Workspace.owner_id == user_id))
            workspace = res.scalar_one()
            workspace_id = workspace.id
        print(f"3. Using auto-created Personal Workspace: {workspace_id}")

        # Create password-protected shortened URL
        print("4. Creating shortened URL with password protection...")
        url_payload = {
            "original_url": "https://httpbin.org/get",
            "workspace_id": workspace_id,
            "password": "supersecret",
            "custom_alias": f"custom{ts}"
        }
        url_response = await client.post("/api/v1/urls/", json=url_payload, headers=headers)
        assert url_response.status_code == 201
        url_data = url_response.json()
        short_code = url_data["short_code"]
        print(f"   [SUCCESS] Created shortened URL. Short Code: {short_code}")

        # Check Redirection without password
        print("5. Requesting redirect without password...")
        red_response_no_pwd = await client.get(f"/{short_code}", follow_redirects=False)
        assert red_response_no_pwd.status_code == 401
        assert "Password Protected Link" in red_response_no_pwd.text
        print("   [SUCCESS] Got 401 Unauthorized with password prompt HTML page")

        # Check Redirection with incorrect password
        print("6. Requesting redirect with incorrect password...")
        red_response_wrong_pwd = await client.get(f"/{short_code}?pwd=wrongpwd", follow_redirects=False)
        assert red_response_wrong_pwd.status_code == 401
        assert "Incorrect password. Please try again." in red_response_wrong_pwd.text
        print("   [SUCCESS] Got 401 Unauthorized with password error HTML page")

        # Check Redirection with correct password
        print("7. Requesting redirect with correct password...")
        red_response_correct_pwd = await client.get(f"/{short_code}?pwd=supersecret", follow_redirects=False)
        assert red_response_correct_pwd.status_code == 302
        assert red_response_correct_pwd.headers["location"] == "https://httpbin.org/get"
        print("   [SUCCESS] Got 302 Found redirecting to https://httpbin.org/get")

        # Verify Redis cache has been populated
        print("8. Checking Redis cache...")
        cached_data = await redis_client.get(f"url:{short_code}")
        assert cached_data is not None
        print(f"   [SUCCESS] Found cached URL metadata in Redis: {cached_data}")

        # Clean up DB
        print("9. Cleaning up test data from Neon PostgreSQL...")
        async with AsyncSessionLocal() as db:
            await db.execute(delete(URL).where(URL.short_code == short_code))
            await db.execute(delete(Workspace).where(Workspace.id == workspace_id))
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()
        print("   [SUCCESS] Deleted test URL, Workspace, and User.")

        # Clean up Redis cache
        print("10. Cleaning up Redis cache...")
        await redis_client.delete(f"url:{short_code}")
        print("    [SUCCESS] Invalidated Redis cache.")

        print("\n--- ALL INTEGRATION TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    asyncio.run(run_integration_tests())
