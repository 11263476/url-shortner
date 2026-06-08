import asyncio
import sys
from sqlalchemy import select

sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.core.database import AsyncSessionLocal
from src.models.analytics import URLAnalyticsSummary

async def check():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(URLAnalyticsSummary))
        rows = res.scalars().all()
        for r in rows:
            print(f"URL ID: {r.url_id} | Total Clicks: {r.total_clicks} | Unique Clicks: {r.unique_clicks} | Last Clicked: {r.last_clicked_at}")

if __name__ == "__main__":
    asyncio.run(check())
