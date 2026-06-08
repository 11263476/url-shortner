from sqlalchemy import select, and_, or_

from src.repositories.base import BaseRepository
from src.models.workspace import Workspace
from src.models.workspace_member import WorkspaceMember


class WorkspaceRepository(BaseRepository[Workspace]):
    def __init__(self, db):
        super().__init__(Workspace, db)

    async def get_user_workspaces(self, user_id: int) -> list[Workspace]:
        owned = await self.get_many(owner_id=user_id)
        member_rows = await self.db.execute(
            select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user_id)
        )
        member_ids = [row[0] for row in member_rows.all() if row[0] not in {w.id for w in owned}]
        if not member_ids:
            return owned
        result = await self.db.execute(
            select(Workspace).where(Workspace.id.in_(member_ids))
        )
        return owned + list(result.scalars().all())

    async def verify_access(self, workspace_id: int, user_id: int) -> Workspace | None:
        result = await self.db.execute(
            select(Workspace).where(
                and_(Workspace.id == workspace_id, Workspace.owner_id == user_id)
            )
        )
        workspace = result.scalar_one_or_none()
        if workspace:
            return workspace
        is_member = await self.db.execute(
            select(WorkspaceMember).where(
                and_(
                    WorkspaceMember.workspace_id == workspace_id,
                    WorkspaceMember.user_id == user_id,
                )
            )
        )
        if is_member.scalar_one_or_none():
            return await self.get(workspace_id)
        return None

    async def create_default(self, user_id: int) -> Workspace:
        return await self.create(name="Personal Workspace", owner_id=user_id)
