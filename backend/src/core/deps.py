from fastapi import Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import decode_token
from src.core.redis import redis_client
from src.models.user import User
from src.repositories import UserRepository, URLRepository, WorkspaceRepository
from src.repositories.folder_repository import FolderRepository
from src.repositories.tag_repository import TagRepository
from src.repositories.analytics_repository import AnalyticsRepository
from src.repositories.api_key_repository import APIKeyRepository
from src.repositories.favorite_repository import FavoriteRepository
from src.repositories.workspace_member_repository import WorkspaceMemberRepository
from src.repositories.workspace_invite_repository import WorkspaceInviteRepository
from src.repositories.audit_log_repository import AuditLogRepository
from src.repositories.webhook_repository import WebhookRepository
from src.services.auth_service import AuthService
from src.services.url_service import URLService
from src.services.workspace_service import WorkspaceService
from src.services.folder_service import FolderService
from src.services.tag_service import TagService
from src.services.favorite_service import FavoriteService
from src.services.analytics_service import AnalyticsService
from src.services.api_key_service import APIKeyService
from src.services.bulk_service import BulkService
from src.services.audit_service import AuditService
from src.services.webhook_service import WebhookService
from src.services.redirect_service import RedirectService
from src.events.dispatcher import KafkaEventDispatcher
from src.errors import InvalidToken, TokenRevoked, UserNotFound


class PaginationParams:
    """Reusable pagination dependency — skip, limit, sort."""
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(20, ge=1, le=100, description="Max records per page"),
        sort_by: str = Query("created_at", description="Sort field"),
        sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort direction"),
    ):
        self.skip = skip
        self.limit = limit
        self.sort_by = sort_by
        self.sort_order = sort_order

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    is_blacklisted = await redis_client.get(f"jwt:blacklist:{token}")
    if is_blacklisted:
        raise TokenRevoked()
    payload = decode_token(token)
    user_id: int = payload.get("sub")
    token_type: str = payload.get("type")
    if not user_id or token_type != "access":
        raise InvalidToken()
    user = await UserRepository(db).get(int(user_id))
    if not user:
        raise UserNotFound()
    return user


async def get_audit_service(db: AsyncSession = Depends(get_db)) -> AuditService:
    return AuditService(
        repo=AuditLogRepository(db),
        workspace_repo=WorkspaceRepository(db),
    )


async def get_webhook_service(db: AsyncSession = Depends(get_db)) -> WebhookService:
    return WebhookService(
        db=db,
        repo=WebhookRepository(db),
        workspace_repo=WorkspaceRepository(db),
    )


async def get_url_service(
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
    webhooks: WebhookService = Depends(get_webhook_service),
) -> URLService:
    return URLService(
        db=db,
        url_repo=URLRepository(db),
        workspace_repo=WorkspaceRepository(db),
        folder_repo=FolderRepository(db),
        tag_repo=TagRepository(db),
        audit=audit,
        webhooks=webhooks,
        event_dispatcher=KafkaEventDispatcher(),
    )


async def get_workspace_service(
    db: AsyncSession = Depends(get_db),
    audit: AuditService = Depends(get_audit_service),
    webhook_svc: WebhookService = Depends(get_webhook_service),
) -> WorkspaceService:
    return WorkspaceService(
        repo=WorkspaceRepository(db),
        member_repo=WorkspaceMemberRepository(db),
        invite_repo=WorkspaceInviteRepository(db),
        user_repo=UserRepository(db),
        audit=audit,
        webhook_svc=webhook_svc,
    )


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(
        user_repo=UserRepository(db),
        workspace_repo=WorkspaceRepository(db),
    )


async def get_folder_service(db: AsyncSession = Depends(get_db)) -> FolderService:
    return FolderService(
        repo=FolderRepository(db),
        workspace_repo=WorkspaceRepository(db),
    )


async def get_tag_service(db: AsyncSession = Depends(get_db)) -> TagService:
    return TagService(
        repo=TagRepository(db),
        workspace_repo=WorkspaceRepository(db),
    )


async def get_favorite_service(db: AsyncSession = Depends(get_db)) -> FavoriteService:
    return FavoriteService(
        repo=FavoriteRepository(db),
        url_repo=URLRepository(db),
    )


async def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(
        url_repo=URLRepository(db),
        analytics_repo=AnalyticsRepository(db),
    )


async def get_api_key_service(db: AsyncSession = Depends(get_db)) -> APIKeyService:
    return APIKeyService(
        repo=APIKeyRepository(db),
        user_repo=UserRepository(db),
    )


async def get_bulk_service(db: AsyncSession = Depends(get_db)) -> BulkService:
    return BulkService(
        db=db,
        url_repo=URLRepository(db),
        workspace_repo=WorkspaceRepository(db),
    )


async def get_redirect_service(db: AsyncSession = Depends(get_db)) -> RedirectService:
    return RedirectService(
        url_repo=URLRepository(db),
        workspace_repo=WorkspaceRepository(db),
        events=KafkaEventDispatcher(),
    )
