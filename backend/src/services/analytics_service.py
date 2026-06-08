from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.url_repository import URLRepository
from src.repositories.analytics_repository import AnalyticsRepository
from src.documents.click_event import ClickEvent
from src.repositories.workspace_repository import WorkspaceRepository
from src.errors import URLNotFound


class AnalyticsService:
    def __init__(self, url_repo: URLRepository, analytics_repo: AnalyticsRepository):
        self.url_repo = url_repo
        self.analytics_repo = analytics_repo

    async def _get_url_and_verify(self, short_code: str, user_id: int):
        url = await self.url_repo.get_by_short_code(short_code)
        if not url:
            raise URLNotFound()
        return url

    async def get_summary(self, short_code: str, user_id: int):
        url = await self._get_url_and_verify(short_code, user_id)
        summary = await self.analytics_repo.get_by_url_id(url.id)
        if not summary:
            return {"short_code": short_code, "total_clicks": 0, "unique_clicks": 0, "last_clicked_at": None}
        return {
            "short_code": short_code,
            "total_clicks": summary.total_clicks,
            "unique_clicks": summary.unique_clicks,
            "last_clicked_at": summary.last_clicked_at,
        }

    async def get_timeseries(self, short_code: str, user_id: int, days: int = 7):
        url = await self._get_url_and_verify(short_code, user_id)
        since = datetime.utcnow() - timedelta(days=days)
        pipeline = [
            {"$match": {"short_code": short_code, "clicked_at": {"$gte": since}}},
            {"$group": {"_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$clicked_at"}}, "clicks": {"$sum": 1}}},
            {"$sort": {"_id": 1}},
        ]
        data = await ClickEvent.aggregate(pipeline).to_list()
        return {
            "short_code": short_code,
            "days": days,
            "data": [{"date": item["_id"], "clicks": item["clicks"]} for item in data],
        }
