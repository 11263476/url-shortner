from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
import secrets

from src.repositories.workspace_repository import WorkspaceRepository
from src.repositories.workspace_member_repository import WorkspaceMemberRepository
from src.repositories.workspace_invite_repository import WorkspaceInviteRepository
from src.repositories.user_repository import UserRepository
from src.models.workspace_member import MemberRole
from src.services.audit_service import AuditService
from src.services.webhook_service import WebhookService
from src.errors import (
    WorkspaceNotFound, OnlyAdminCanInvite, PendingInviteExists,
    CannotInviteOwner, AlreadyMember, InviteNotFound, InviteExpired,
    InviteEmailMismatch, CannotRemoveOwner, OnlyOwnerCanChangeRoles,
    MemberNotFound, BadRequestError,
)


class WorkspaceService:
    def __init__(
        self,
        repo: WorkspaceRepository,
        member_repo: WorkspaceMemberRepository,
        invite_repo: WorkspaceInviteRepository,
        user_repo: UserRepository,
        audit: AuditService,
        webhook_svc: WebhookService,
    ):
        self.repo = repo
        self.member_repo = member_repo
        self.invite_repo = invite_repo
        self.user_repo = user_repo
        self.audit = audit
        self.webhook_svc = webhook_svc

    async def create(self, name: str, user_id: int):
        ws = await self.repo.create(name=name, owner_id=user_id)
        await self.member_repo.add_member(ws.id, user_id, MemberRole.admin)
        await self.audit.log(
            actor_id=user_id, action="create", resource_type="workspace",
            resource_id=ws.id, after={"name": ws.name},
        )

        await self.webhook_svc.deliver_event(ws.id, "workspace.created", {
            "workspace_id": ws.id, "name": ws.name, "user_id": user_id,
        })

        return ws

    async def list(self, user_id: int):
        return await self.repo.get_user_workspaces(user_id)

    async def get(self, id: int, user_id: int):
        workspace = await self.repo.verify_access(id, user_id)
        if not workspace:
            raise WorkspaceNotFound()
        return workspace

    async def invite(self, workspace_id: int, email: str, role: str, invited_by: int):
        ws = await self.repo.verify_access(workspace_id, invited_by)
        if not ws:
            raise WorkspaceNotFound()
        if ws.owner_id != invited_by:
            member = await self.member_repo.get_member(workspace_id, invited_by)
            if not member or member.role != MemberRole.admin:
                raise OnlyAdminCanInvite()
        existing = await self.invite_repo.get_pending_for_email(workspace_id, email)
        if existing:
            raise PendingInviteExists()
        user = await self.user_repo.get_by_email(email)
        if user:
            if ws.owner_id == user.id:
                raise CannotInviteOwner()
            if await self.member_repo.is_member(workspace_id, user.id):
                raise AlreadyMember()
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        invite = await self.invite_repo.create(
            workspace_id=workspace_id, email=email, invited_by=invited_by,
            token=token, role=role, expires_at=expires_at,
        )
        await self.audit.log(
            actor_id=invited_by, action="invite", resource_type="workspace_invite",
            resource_id=invite.id, after={"email": email, "role": role},
            workspace_id=workspace_id,
        )

        await self.webhook_svc.deliver_event(workspace_id, "workspace.invite_sent", {
            "workspace_id": workspace_id, "email": email, "role": role, "invited_by": invited_by,
        })

        return invite

    async def accept_invite(self, token: str, user_id: int):
        invite = await self.invite_repo.get_by_token(token)
        if not invite:
            raise InviteNotFound()
        if invite.status.name != "pending":
            raise BadRequestError("Invite is no longer valid.")
        if invite.expires_at < datetime.utcnow():
            await self.invite_repo.update(invite.id, status="expired")
            raise InviteExpired()
        user = await self.user_repo.get(user_id)
        if not user or user.email != invite.email:
            raise InviteEmailMismatch()
        if await self.member_repo.is_member(invite.workspace_id, user_id):
            raise AlreadyMember()
        await self.member_repo.add_member(invite.workspace_id, user_id, MemberRole(invite.role))
        await self.invite_repo.accept(token)
        await self.audit.log(
            actor_id=user_id, action="accept_invite", resource_type="workspace_member",
            resource_id=user_id, after={"workspace_id": invite.workspace_id, "role": invite.role},
            workspace_id=invite.workspace_id,
        )

        await self.webhook_svc.deliver_event(invite.workspace_id, "workspace.member_joined", {
            "workspace_id": invite.workspace_id, "user_id": user_id, "role": invite.role,
        })

        return {"detail": "Invite accepted successfully."}

    async def list_invites(self, workspace_id: int, user_id: int):
        ws = await self.repo.verify_access(workspace_id, user_id)
        if not ws:
            raise WorkspaceNotFound()
        return await self.invite_repo.get_workspace_invites(workspace_id)

    async def cancel_invite(self, workspace_id: int, invite_id: int, user_id: int):
        ws = await self.repo.verify_access(workspace_id, user_id)
        if not ws:
            raise WorkspaceNotFound()
        await self.invite_repo.cancel(invite_id)
        await self.audit.log(
            actor_id=user_id, action="cancel_invite", resource_type="workspace_invite",
            resource_id=invite_id, workspace_id=workspace_id,
        )

    async def list_members(self, workspace_id: int, user_id: int):
        ws = await self.repo.verify_access(workspace_id, user_id)
        if not ws:
            raise WorkspaceNotFound()
        return await self.member_repo.get_workspace_members(workspace_id)

    async def remove_member(self, workspace_id: int, member_id: int, user_id: int):
        ws = await self.repo.verify_access(workspace_id, user_id)
        if not ws:
            raise WorkspaceNotFound()
        member = await self.member_repo.get(member_id)
        if not member or member.workspace_id != workspace_id:
            raise MemberNotFound()
        if member.user_id == ws.owner_id:
            raise CannotRemoveOwner()
        await self.member_repo.remove_member(workspace_id, member.user_id)
        await self.audit.log(
            actor_id=user_id, action="remove_member", resource_type="workspace_member",
            resource_id=member.user_id, workspace_id=workspace_id,
        )

    async def update_member_role(self, workspace_id: int, member_id: int, role: MemberRole, user_id: int):
        ws = await self.repo.verify_access(workspace_id, user_id)
        if not ws:
            raise WorkspaceNotFound()
        if ws.owner_id != user_id:
            raise OnlyOwnerCanChangeRoles()
        member = await self.member_repo.get(member_id)
        if not member or member.workspace_id != workspace_id:
            raise MemberNotFound()
        result = await self.member_repo.update_role(workspace_id, member.user_id, role)
        await self.audit.log(
            actor_id=user_id, action="update_role", resource_type="workspace_member",
            resource_id=member.user_id,
            before={"role": member.role.value},
            after={"role": role.value},
            workspace_id=workspace_id,
        )
        return result
