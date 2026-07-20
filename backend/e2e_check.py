import asyncio
from src.core.database import AsyncSessionLocal
from src.core.mongodb import init_mongodb
from src.documents.click_event import ClickEvent
from sqlalchemy import text
from datetime import datetime

async def check():
    # Check MongoDB for analytics worker
    await init_mongodb()
    events = await ClickEvent.find({"short_code": "e2etest"}).to_list()
    print("=== Analytics Worker (MongoDB) ===")
    print("Click events for e2etest:", len(events))
    for e in events:
        print(f"  event_id={e.event_id} ip={e.ip_address} ua={(e.user_agent or '')[:50]}")

    # Check PostgreSQL for metadata worker
    print("\n=== Metadata Worker (PostgreSQL) ===")
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT short_code, original_url, workspace_id FROM urls WHERE short_code = 'e2etest'"))
        rows = r.fetchall()
        print("URLs:", len(rows))
        for row in rows:
            print(f"  short_code={row[0]} url={row[1]} workspace={row[2]}")

    print("\nDone. Run again after a few seconds if results are empty.")

asyncio.run(check())
