from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert

from src.repositories.base import BaseRepository
from src.models.analytics import URLAnalyticsSummary


class AnalyticsRepository(BaseRepository[URLAnalyticsSummary]):
    def __init__(self, db):
        super().__init__(URLAnalyticsSummary, db)

    async def get_by_url_id(self, url_id: int) -> URLAnalyticsSummary | None:
        return await self.get(url_id)

    async def upsert_click(self, url_id: int, clicked_at) -> None:
        stmt = insert(URLAnalyticsSummary).values(
            url_id=url_id, total_clicks=1, unique_clicks=1, last_clicked_at=clicked_at
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["url_id"],
            set_={
                "total_clicks": URLAnalyticsSummary.total_clicks + 1,
                "last_clicked_at": clicked_at,
            },
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def upsert_rollup(self, url_id: int, total_clicks: int, unique_clicks: int) -> None:
        stmt = insert(URLAnalyticsSummary).values(
            url_id=url_id, total_clicks=total_clicks, unique_clicks=unique_clicks
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["url_id"],
            set_={"total_clicks": total_clicks, "unique_clicks": unique_clicks},
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def delete_by_url_id(self, url_id: int) -> None:
        await self.db.execute(
            delete(URLAnalyticsSummary).where(URLAnalyticsSummary.url_id == url_id)
        )
        await self.db.commit()

    async def delete_by_url_ids(self, url_ids: list[int]) -> None:
        await self.db.execute(
            delete(URLAnalyticsSummary).where(URLAnalyticsSummary.url_id.in_(url_ids))
        )
        await self.db.commit()
