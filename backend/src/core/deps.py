import time

from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.redis import redis_client
from src.core.security import decode_token, verify_password
from src.models.user import User

# In-memory cache for JWT blacklist checks — avoids Redis REST round-trip on every request
_blacklist_cache: dict[str, float] = {}
_BLACKLIST_CACHE_TTL = 60  # seconds
from src.errors import InvalidToken, TokenRevoked, UnauthorizedError, UserNotFound
from src.events.dispatcher import KafkaEventDispatcher
from src.models.api_key import APIKeyStatus
from src.repositories import URLRepository, UserRepository, WorkspaceRepository
from src.repositories.analytics_repository import AnalyticsRepository
from src.repositories.api_key_repository import APIKeyRepository
from src.repositories.audit_log_repository import AuditLogRepository
from src.repositories.favorite_repository import FavoriteRepository
from src.repositories.folder_repository import FolderRepository
from src.repositories.tag_repository import TagRepository
from src.repositories.webhook_receiver_repository import WebhookReceivedEventRepository
from src.repositories.webhook_repository import WebhookRepository
from src.repositories.workspace_invite_repository import WorkspaceInviteRepository
from src.repositories.workspace_member_repository import WorkspaceMemberRepository
from src.services.analytics_service import AnalyticsService
from src.services.api_key_service import APIKeyService
from src.services.audit_service import AuditService
from src.services.auth_service import AuthService
from src.services.bulk_service import BulkService
from src.services.favorite_service import FavoriteService
from src.services.folder_service import FolderService
from src.services.redirect_service import RedirectService
from src.services.tag_service import TagService
from src.services.url_service import URLService
from src.services.webhook_receiver_service import WebhookReceiverService
from src.services.webhook_service import WebhookService
from src.services.workspace_service import WorkspaceService


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

    # API key auth (lf_ prefix)
    if token.startswith("lf_"):
        prefix = token[:8]
        key_record = await APIKeyRepository(db).get_by_prefix(prefix)
        if not key_record:
            raise UnauthorizedError("Invalid API key")
        if key_record.status != APIKeyStatus.active:
            raise UnauthorizedError("API key has been revoked")
        if not verify_password(token, key_record.key_hash):
            raise UnauthorizedError("Invalid API key")
        if key_record.expires_at and key_record.expires_at < __import__("datetime").datetime.utcnow():
            raise UnauthorizedError("API key has expired")
        key_record.last_used_at = __import__("datetime").datetime.utcnow()
        await db.commit()
        user = await UserRepository(db).get(key_record.user_id)
        if not user:
            raise UserNotFound()
        return user

    # JWT auth
    now = time.time()
    cached = _blacklist_cache.get(token)
    if cached is not None and cached > now:
        raise TokenRevoked()
    if cached is None:
        is_blacklisted = await redis_client.get(f"jwt:blacklist:{token}")
        if is_blacklisted:
            _blacklist_cache[token] = now + _BLACKLIST_CACHE_TTL
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
        workspace_repo=WorkspaceRepository(db),
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


async def get_webhook_receiver_service(db: AsyncSession = Depends(get_db)) -> WebhookReceiverService:
    return WebhookReceiverService(
        db=db,
        repo=WebhookReceivedEventRepository(db),
        webhook_repo=WebhookRepository(db),
        workspace_repo=WorkspaceRepository(db),
    )
