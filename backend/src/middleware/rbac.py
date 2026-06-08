from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select

from src.core.database import AsyncSessionLocal
from src.models.workspace_member import WorkspaceMember, MemberRole
from src.core.audit_context import audit_ctx_var


WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

HIERARCHY = {
    MemberRole.admin: 3,
    MemberRole.editor: 2,
    MemberRole.viewer: 1,
}


class RBACMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method not in WRITE_METHODS or not request.url.path.startswith("/api/v1/"):
            return await call_next(request)

        if not hasattr(request.state, "user_id") or not request.state.user_id:
            return await call_next(request)

        workspace_id = self._extract_workspace_id(request.url.path)
        if workspace_id is None:
            return await call_next(request)

        allowed = await require_role(workspace_id, request.state.user_id, MemberRole.editor)
        if not allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Editor role or higher required.")

        return await call_next(request)

    def _extract_workspace_id(self, path: str) -> int | None:
        parts = path.rstrip("/").split("/")
        for i, part in enumerate(parts):
            if part in ("workspaces", "folders", "urls", "tags") and i + 1 < len(parts):
                try:
                    return int(parts[i + 1])
                except ValueError:
                    continue
        return None


async def require_role(workspace_id: int, user_id: int, min_role: MemberRole) -> bool:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        if HIERARCHY.get(member.role, 0) < HIERARCHY.get(min_role, 0):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires {min_role.value} role or higher.")
        return True
