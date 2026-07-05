from sqlalchemy import and_, select

from src.models.webhook import Webhook
from src.repositories.base import BaseRepository


class WebhookRepository(BaseRepository[Webhook]):
    def __init__(self, db):
        super().__init__(Webhook, db)

    async def get_workspace_webhooks(self, workspace_id: int) -> list[Webhook]:
        return await self.get_many(workspace_id=workspace_id)

    async def get_active_by_event(self, workspace_id: int, event: str) -> list[Webhook]:
        result = await self.db.execute(
            select(Webhook).where(
                and_(
                    Webhook.workspace_id == workspace_id,
                    Webhook.is_active == True,
                    Webhook.events.contains(event),
                )
            )
        )
        return list(result.scalars().all())
