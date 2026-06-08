from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.url_repository import URLRepository
from src.repositories.workspace_repository import WorkspaceRepository
from src.repositories.folder_repository import FolderRepository
from src.repositories.tag_repository import TagRepository
from src.core.security import hash_password
from src.core.redis import delete_url_cache
from src.events.dispatcher import EventDispatcher
from src.utils.base62 import generate_short_code
from src.models.url import URL, URLStatus
from src.services.audit_service import AuditService
from src.services.webhook_service import WebhookService
from src.errors import (
    WorkspaceNotFound, FolderNotInWorkspace, AliasReserved,
    AliasConflict, CannotGenerateShortCode, URLNotFound,
)

RESERVED_ALIASES = {"admin", "api", "login", "register", "logout", "verify", "reset", "health", "metrics", "dashboard"}


class URLService:
    def __init__(
        self,
        db: AsyncSession,
        url_repo: URLRepository,
        workspace_repo: WorkspaceRepository,
        folder_repo: FolderRepository,
        tag_repo: TagRepository,
        audit: AuditService,
        webhooks: WebhookService,
        event_dispatcher: EventDispatcher,
    ):
        self.db = db
        self.url_repo = url_repo
        self.workspace_repo = workspace_repo
        self.folder_repo = folder_repo
        self.tag_repo = tag_repo
        self.audit = audit
        self.webhooks = webhooks
        self.event_dispatcher = event_dispatcher

    async def _verify_workspace_access(self, workspace_id: int, user_id: int):
        ws = await self.workspace_repo.verify_access(workspace_id, user_id)
        if not ws:
            raise WorkspaceNotFound()

    async def create(self, payload, user_id: int) -> URL:
        await self._verify_workspace_access(payload.workspace_id, user_id)

        if payload.folder_id:
            if not await self.folder_repo.folder_belongs_to_workspace(payload.folder_id, payload.workspace_id):
                raise FolderNotInWorkspace()

        short_code = None
        if payload.custom_alias:
            alias = payload.custom_alias.strip().lower()
            if alias in RESERVED_ALIASES:
                raise AliasReserved(alias)
            if await self.url_repo.alias_exists(alias):
                raise AliasConflict()
            short_code = alias
        else:
            for _ in range(5):
                candidate = generate_short_code()
                if not await self.url_repo.alias_exists(candidate):
                    short_code = candidate
                    break
            if not short_code:
                raise CannotGenerateShortCode()

        password_hash = hash_password(payload.password) if payload.password else None

        url = URL(
            short_code=short_code,
            original_url=str(payload.original_url),
            user_id=user_id,
            workspace_id=payload.workspace_id,
            folder_id=payload.folder_id,
            custom_alias=payload.custom_alias,
            domain=payload.domain,
            password_hash=password_hash,
            is_ab_test=payload.is_ab_test,
            is_one_time=payload.is_one_time,
            ios_url=str(payload.ios_url) if payload.ios_url else None,
            android_url=str(payload.android_url) if payload.android_url else None,
            expires_at=payload.expires_at,
            status=URLStatus.active,
        )

        if payload.tags:
            db_tags = []
            for tag_name in set(payload.tags):
                tag = await self.tag_repo.get_or_create(tag_name, payload.workspace_id)
                db_tags.append(tag)
            url.tags = db_tags

        self.db.add(url)
        await self.db.commit()
        await self.db.refresh(url)

        try:
            await self.event_dispatcher.dispatch("url-created", {
                "short_code": url.short_code,
                "original_url": url.original_url,
                "workspace_id": url.workspace_id,
                "user_id": url.user_id,
                "base_url": "http://localhost:8000",
            }, key=url.short_code)
        except Exception as e:
            print(f"[WARNING] Failed to publish url-created event: {e}")

        await self.audit.log(
            actor_id=user_id, action="create", resource_type="url",
            resource_id=url.id, after={"short_code": url.short_code, "original_url": url.original_url},
            workspace_id=payload.workspace_id,
        )

        await self.webhooks.deliver_event(payload.workspace_id, "url.created", {
            "short_code": url.short_code, "original_url": url.original_url,
            "workspace_id": url.workspace_id, "user_id": user_id,
        })

        return url

    async def list(self, workspace_id: int, user_id: int, **filters) -> list[URL]:
        await self._verify_workspace_access(workspace_id, user_id)
        return await self.url_repo.get_workspace_urls(workspace_id, **filters)

    async def get(self, id: int, user_id: int) -> URL:
        url = await self.url_repo.get(id)
        if not url or url.status == URLStatus.deleted:
            raise URLNotFound()
        await self._verify_workspace_access(url.workspace_id, user_id)
        return url

    async def update(self, id: int, payload, user_id: int) -> URL:
        url = await self.get(id, user_id)
        before = {"original_url": url.original_url, "status": url.status.value, "folder_id": url.folder_id}
        if payload.folder_id is not None:
            if not await self.folder_repo.folder_belongs_to_workspace(payload.folder_id, url.workspace_id):
                raise FolderNotInWorkspace()
            url.folder_id = payload.folder_id
        if payload.original_url is not None:
            url.original_url = str(payload.original_url)
        if payload.domain is not None:
            url.domain = payload.domain
        if payload.password is not None:
            url.password_hash = hash_password(payload.password) if payload.password else None
        if payload.is_ab_test is not None:
            url.is_ab_test = payload.is_ab_test
        if payload.ios_url is not None:
            url.ios_url = str(payload.ios_url) if payload.ios_url else None
        if payload.android_url is not None:
            url.android_url = str(payload.android_url) if payload.android_url else None
        if payload.expires_at is not None:
            url.expires_at = payload.expires_at
        if payload.status is not None:
            url.status = payload.status
        if payload.tags is not None:
            db_tags = []
            for tag_name in set(payload.tags):
                tag = await self.tag_repo.get_or_create(tag_name, url.workspace_id)
                db_tags.append(tag)
            url.tags = db_tags
        await self.db.commit()
        await delete_url_cache(url.short_code)
        await self.db.refresh(url)
        after = {"original_url": url.original_url, "status": url.status.value, "folder_id": url.folder_id}
        await self.audit.log(
            actor_id=user_id, action="update", resource_type="url",
            resource_id=url.id, before=before, after=after,
            workspace_id=url.workspace_id,
        )

        await self.webhooks.deliver_event(url.workspace_id, "url.updated", {
            "short_code": url.short_code, "original_url": url.original_url,
            "workspace_id": url.workspace_id, "user_id": user_id,
        })

        return url

    async def delete(self, id: int, user_id: int) -> None:
        url = await self.get(id, user_id)
        await self.url_repo.soft_delete(id)
        await delete_url_cache(url.short_code)
        await self.audit.log(
            actor_id=user_id, action="delete", resource_type="url",
            resource_id=url.id, before={"short_code": url.short_code, "original_url": url.original_url},
            workspace_id=url.workspace_id,
        )

        await self.webhooks.deliver_event(url.workspace_id, "url.deleted", {
            "short_code": url.short_code, "original_url": url.original_url,
            "workspace_id": url.workspace_id, "user_id": user_id,
        })
