import asyncio
import sys
import httpx
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select

sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.core.database import AsyncSessionLocal
from src.models.url import URL, URLStatus
from src.core.redis import get_url_cache, init_redis
from src.workers.expiry_worker import scan_and_expire_urls

BASE_URL = "http://localhost:8000"

async def test_expiry():
    print("[INFO] Starting Expiry Worker Test...")
    await init_redis()
    
    async with httpx.AsyncClient() as client:
        # 1. Register & Login
        email = f"test_exp_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        
        await client.post(f"{BASE_URL}/api/v1/auth/register", json={"email": email, "password": password})
        login_res = await client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get Workspace ID
        ws_res = await client.get(f"{BASE_URL}/api/v1/workspaces/", headers=headers)
        workspace_id = ws_res.json()[0]["id"]
        
        # 3. Create URL with expires_at in the past
        past_time = datetime.utcnow() - timedelta(minutes=5)
        url_res = await client.post(
            f"{BASE_URL}/api/v1/urls/",
            json={
                "original_url": "https://fastapi.tiangolo.com",
                "workspace_id": workspace_id,
                "expires_at": past_time.isoformat()
            },
            headers=headers
        )
        url_data = url_res.json()
        short_code = url_data["short_code"]
        url_id = url_data["id"]
        print(f"[OK] Created URL: {short_code} (ID: {url_id}), Expired at: {past_time}")
        
        # 4. Trigger redirect to cache it
        print("   Triggering redirect to populate Redis cache...")
        # (This should return 410 since redirect route checks expiration, but it will still populate the cache first)
        await client.get(f"{BASE_URL}/{short_code}")
        
        cached_data = await get_url_cache(short_code)
        print(f"   Cached data before scan: {cached_data is not None}")
        
        # 5. Run Expiry Scan
        print("[INFO] Running expiry worker scan...")
        await scan_and_expire_urls()
        
        # 6. Verify Postgres status and Redis cache
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(URL).where(URL.id == url_id))
            url_obj = result.scalar_one_or_none()
            
            cached_data_after = await get_url_cache(short_code)
            print(f"[DATA] Postgres Status: {url_obj.status if url_obj else 'None'}")
            print(f"[DATA] Cached data after scan: {cached_data_after is not None}")
            
            if url_obj and url_obj.status == URLStatus.disabled and cached_data_after is None:
                print("[SUCCESS] Expiry worker successfully updated Postgres status to disabled and evicted URL from Redis cache!")
            else:
                print("[FAIL] Expiry worker failed to process expiration correctly.")

if __name__ == "__main__":
    asyncio.run(test_expiry())
