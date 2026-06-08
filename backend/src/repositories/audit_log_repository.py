from sqlalchemy import select, and_

from src.repositories.base import BaseRepository
from src.models.audit_log import AuditLog


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, db):
        super().__init__(AuditLog, db)

    async def log(
        self,
        actor_id: int | None,
        action: str,
        resource_type: str,
        resource_id: int | None = None,
        before_state: str | None = None,
        after_state: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        workspace_id: int | None = None,
    ) -> AuditLog:
        return await self.create(
            actor_id=actor_id, action=action, resource_type=resource_type,
            resource_id=resource_id, before_state=before_state,
            after_state=after_state, ip_address=ip_address,
            user_agent=user_agent, workspace_id=workspace_id,
        )

    async def get_workspace_logs(
        self, workspace_id: int, skip: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        return await self.get_many(workspace_id=workspace_id, skip=skip, limit=limit)

    async def get_resource_logs(
        self, resource_type: str, resource_id: int, skip: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        return await self.get_many(resource_type=resource_type, resource_id=resource_id, skip=skip, limit=limit)

    async def get_actor_logs(
        self, actor_id: int, skip: int = 0, limit: int = 100
    ) -> list[AuditLog]:
        return await self.get_many(actor_id=actor_id, skip=skip, limit=limit)
