from sqlalchemy import select, update, and_, or_

from src.repositories.base import BaseRepository
from src.models.url import URL, URLStatus
from src.models.tag import Tag


class URLRepository(BaseRepository[URL]):
    def __init__(self, db):
        super().__init__(URL, db)

    async def get_by_short_code(self, short_code: str) -> URL | None:
        return await self.get_by(short_code=short_code)

    async def get_by_custom_alias(self, alias: str) -> URL | None:
        return await self.get_by(custom_alias=alias)

    async def alias_exists(self, alias: str) -> bool:
        result = await self.db.execute(
            select(URL).where(or_(URL.custom_alias == alias, URL.short_code == alias))
        )
        return result.scalar_one_or_none() is not None

    async def get_workspace_urls(
        self,
        workspace_id: int,
        folder_id: int | None = None,
        tag: str | None = None,
        search: str | None = None,
        status_filter: URLStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[URL]:
        query = select(URL).where(
            and_(URL.workspace_id == workspace_id, URL.status != URLStatus.deleted)
        )
        if folder_id is not None:
            query = query.where(URL.folder_id == folder_id)
        if status_filter:
            query = query.where(URL.status == status_filter)
        if tag:
            query = query.join(URL.tags).where(Tag.name == tag.strip().lower())
        if search:
            term = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    URL.original_url.ilike(term),
                    URL.short_code.ilike(term),
                    URL.custom_alias.ilike(term),
                )
            )
        query = query.order_by(URL.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def soft_delete(self, id: int) -> None:
        await self.db.execute(update(URL).where(URL.id == id).values(status=URLStatus.deleted))
        await self.db.commit()

    async def bulk_update(self, url_ids: list[int], workspace_id: int, **values) -> None:
        await self.db.execute(
            update(URL)
            .where(and_(URL.id.in_(url_ids), URL.workspace_id == workspace_id))
            .values(**values)
        )
        await self.db.commit()

    async def get_short_codes_by_ids(self, url_ids: list[int], workspace_id: int) -> list[tuple[int, str]]:
        result = await self.db.execute(
            select(URL.id, URL.short_code).where(
                and_(URL.id.in_(url_ids), URL.workspace_id == workspace_id)
            )
        )
        return result.all()

    async def get_url_id_by_short_code(self, short_code: str) -> int | None:
        result = await self.db.execute(select(URL.id).where(URL.short_code == short_code))
        return result.scalar_one_or_none()
