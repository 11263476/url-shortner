import asyncio
import sys
import httpx
import uuid
from sqlalchemy import select

sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.core.database import AsyncSessionLocal
from src.models.url import URL
from src.core.mongodb import init_mongodb
from src.documents.click_event import ClickEvent
from src.workers.cleanup_worker import run_cleanup

BASE_URL = "http://localhost:8000"

async def test_cleanup():
    print("[INFO] Starting Cleanup Worker Test...")
    await init_mongodb()
    
    async with httpx.AsyncClient() as client:
        # 1. Register & Login
        email = f"test_cln_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        
        await client.post(f"{BASE_URL}/api/v1/auth/register", json={"email": email, "password": password})
        login_res = await client.post(f"{BASE_URL}/api/v1/auth/login", json={"email": email, "password": password})
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get Workspace ID
        ws_res = await client.get(f"{BASE_URL}/api/v1/workspaces/", headers=headers)
        workspace_id = ws_res.json()[0]["id"]
        
        # 3. Create URL
        url_res = await client.post(
            f"{BASE_URL}/api/v1/urls/",
            json={
                "original_url": "https://fastapi.tiangolo.com",
                "workspace_id": workspace_id
            },
            headers=headers
        )
        url_data = url_res.json()
        short_code = url_data["short_code"]
        url_id = url_data["id"]
        print(f"[OK] Created URL: {short_code} (ID: {url_id})")
        
        # 4. Trigger redirect to log click event
        print("   Triggering redirect to create MongoDB event log...")
        await client.get(f"{BASE_URL}/{short_code}")
        
        # Wait 4 seconds for Kafka
        print("   Waiting 4 seconds for event to reach MongoDB...")
        await asyncio.sleep(4)
        
        mongo_events_before = await ClickEvent.find(ClickEvent.short_code == short_code).to_list()
        print(f"   MongoDB event count before cleanup: {len(mongo_events_before)}")
        
        # 5. Soft-delete the URL
        print("[INFO] Soft-deleting URL in PostgreSQL...")
        del_res = await client.delete(f"{BASE_URL}/api/v1/urls/{url_id}", headers=headers)
        if del_res.status_code != 200:
            print(f"[FAIL] Soft-delete failed: {del_res.status_code} - {del_res.text}")
            return
            
        # 6. Run Cleanup scan
        print("[INFO] Running cleanup worker scan...")
        await run_cleanup()
        
        # 7. Assert database states
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(URL).where(URL.id == url_id))
            url_obj = result.scalar_one_or_none()
            
            mongo_events_after = await ClickEvent.find(ClickEvent.short_code == short_code).to_list()
            
            print(f"[DATA] Postgres record exists? {url_obj is not None}")
            print(f"[DATA] MongoDB click count after: {len(mongo_events_after)}")
            
            if url_obj is None and len(mongo_events_after) == 0:
                print("[SUCCESS] Cleanup worker successfully purged PostgreSQL URL record and associated MongoDB click logs!")
            else:
                print("[FAIL] Cleanup worker did not purge records correctly.")

if __name__ == "__main__":
    asyncio.run(test_cleanup())
