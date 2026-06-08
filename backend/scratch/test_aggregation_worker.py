import asyncio
import sys
import httpx
import uuid
from sqlalchemy import select

sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.core.database import AsyncSessionLocal
from src.models.analytics import URLAnalyticsSummary
from src.models.url import URL
from src.workers.aggregation_worker import run_aggregation_rollup

BASE_URL = "http://localhost:8000"

async def test_aggregation():
    print("[INFO] Starting Aggregation Worker Test...")
    
    async with httpx.AsyncClient() as client:
        # 1. Register & Login
        email = f"test_agg_{uuid.uuid4().hex[:8]}@example.com"
        password = "Password123!"
        
        reg_res = await client.post(f"{BASE_URL}/api/v1/auth/register", json={
            "email": email,
            "password": password
        })
        if reg_res.status_code != 201:
            print(f"[FAIL] Register failed: {reg_res.status_code}")
            return
            
        login_res = await client.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
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
        
        # 4. Simulate Clicks with different IPs
        # Click 1: IP 1.1.1.1
        print("   Simulating Click 1 from IP 1.1.1.1...")
        await client.get(f"{BASE_URL}/{short_code}", headers={"X-Forwarded-For": "1.1.1.1"})
        
        # Click 2: IP 1.1.1.1 (duplicate IP)
        print("   Simulating Click 2 from IP 1.1.1.1...")
        await client.get(f"{BASE_URL}/{short_code}", headers={"X-Forwarded-For": "1.1.1.1"})
        
        # Click 3: IP 2.2.2.2 (new IP)
        print("   Simulating Click 3 from IP 2.2.2.2...")
        await client.get(f"{BASE_URL}/{short_code}", headers={"X-Forwarded-For": "2.2.2.2"})
        
        print("[INFO] Waiting 4 seconds for Kafka to dispatch events to MongoDB...")
        await asyncio.sleep(4)
        
        # 5. Run Aggregation Rollup
        print("[INFO] Running rollup function...")
        await run_aggregation_rollup()
        
        # 6. Verify Postgres URLAnalyticsSummary
        print("[INFO] Fetching analytics summary from PostgreSQL...")
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(URLAnalyticsSummary).where(URLAnalyticsSummary.url_id == url_id)
            )
            summary = result.scalar_one_or_none()
            
            if summary:
                print(f"[DATA] Postgres Summary - Total Clicks: {summary.total_clicks}, Unique Clicks: {summary.unique_clicks}")
                if summary.total_clicks == 3 and summary.unique_clicks == 2:
                    print("[SUCCESS] Aggregation worker computed exact metrics (3 total, 2 unique) successfully!")
                else:
                    print(f"[FAIL] Expected 3 total clicks and 2 unique clicks, but got: {summary.total_clicks} total, {summary.unique_clicks} unique.")
            else:
                print("[FAIL] No analytics summary record found in PostgreSQL for this URL.")

if __name__ == "__main__":
    asyncio.run(test_aggregation())
