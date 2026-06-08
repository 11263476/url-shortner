import asyncio
import httpx
import time
import json
import uuid

BASE_URL = "http://localhost:8000"

async def test_analytics_pipeline():
    print("[INFO] Starting Analytics Pipeline Test")
    
    async with httpx.AsyncClient() as client:
        # 1. Register and Login a test user
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        password = "SuperSecretPassword123!"
        
        print(f"\n[1] Registering user: {email}")
        reg_res = await client.post(f"{BASE_URL}/api/v1/auth/register", json={
            "email": email,
            "password": password
        })
        
        if reg_res.status_code != 201:
            print(f"[FAIL] Register failed: {reg_res.status_code} - {reg_res.text}")
            return
            
        print("[1.5] Logging in to get access token...")
        login_res = await client.post(f"{BASE_URL}/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        
        if login_res.status_code != 200:
            print(f"[FAIL] Login failed: {login_res.status_code} - {login_res.text}")
            return
            
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1.6 Fetch User's Workspaces
        print("[1.6] Fetching workspaces...")
        ws_res = await client.get(f"{BASE_URL}/api/v1/workspaces/", headers=headers)
        if ws_res.status_code != 200:
            print(f"[FAIL] Fetching workspaces failed: {ws_res.status_code} - {ws_res.text}")
            return
        
        workspaces = ws_res.json()
        if not workspaces:
            print("[FAIL] No workspaces found for user.")
            return
            
        workspace_id = workspaces[0]["id"]
        print(f"[OK] Using Workspace ID: {workspace_id}")

        # 2. Create a Short URL
        print("\n[2] Creating a short URL...")
        url_res = await client.post(
            f"{BASE_URL}/api/v1/urls/",
            json={
                "original_url": "https://github.com/fastapi/fastapi",
                "workspace_id": workspace_id
            },
            headers=headers
        )
        
        if url_res.status_code != 201:
            print(f"[FAIL] Creating short URL failed: {url_res.status_code} - {url_res.text}")
            return
            
        url_data = url_res.json()
        short_code = url_data["short_code"]
        print(f"[OK] Created Short URL: {BASE_URL}/{short_code}")
        
        # 3. Simulate Clicks
        print("\n[3] Simulating 3 clicks on the short URL...")
        for i in range(3):
            # Using follow_redirects=False to just get the 302
            res = await client.get(
                f"{BASE_URL}/{short_code}", 
                follow_redirects=False,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            )
            print(f"   Click {i+1} -> Status: {res.status_code}")
            
        print("\n[INFO] Polling up to 10 seconds for Kafka event to reach Analytics Worker...")
        summary_res = None
        for attempt in range(10):
            await asyncio.sleep(1)
            summary_res = await client.get(f"{BASE_URL}/api/v1/analytics/{short_code}/summary", headers=headers)
            if summary_res.status_code == 200:
                if summary_res.json().get("total_clicks") == 3:
                    print(f"   Success on attempt {attempt+1}!")
                    break
        
        # 4. Check Analytics Summary (Postgres)
        print("\n[4] Fetching Analytics Summary (Postgres)...")
        if summary_res:
            print(f"[DATA] Summary Data: {json.dumps(summary_res.json(), indent=2)}")
        
        # 5. Check Analytics Timeseries (MongoDB)
        print("\n[5] Fetching Analytics Timeseries (MongoDB)...")
        timeseries_res = await client.get(f"{BASE_URL}/api/v1/analytics/{short_code}/timeseries?days=7", headers=headers)
        print(f"[DATA] Timeseries Data: {json.dumps(timeseries_res.json(), indent=2)}")
        
        if summary_res and summary_res.json().get("total_clicks") == 3:
            print("\n[SUCCESS] The event-driven analytics pipeline works perfectly! Kafka -> Worker -> DBs")
        else:
            print("\n[WARNING] Hmmm, expected 3 total_clicks. Check if the worker is running and connected.")

if __name__ == "__main__":
    asyncio.run(test_analytics_pipeline())
