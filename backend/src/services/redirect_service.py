from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from src.repositories.url_repository import URLRepository
from src.repositories.workspace_repository import WorkspaceRepository
from src.core.security import verify_password
from src.core.redis import get_url_cache, set_url_cache, delete_url_cache, check_rate_limit
from src.events.dispatcher import EventDispatcher
from src.errors.url import URLNotFound, URLDisabled, URLExpired, URLPasswordIncorrect
from src.errors.common import RateLimitError


@dataclass
class RedirectResult:
    destination: str
    url_id: int
    short_code: str
    workspace_id: int
    is_one_time: bool


class RedirectService:
    def __init__(self, url_repo: URLRepository, workspace_repo: WorkspaceRepository, events: EventDispatcher):
        self.url_repo = url_repo
        self.workspace_repo = workspace_repo
        self.events = events

    async def resolve(
        self,
        short_code: str,
        ip: str,
        user_agent: Optional[str],
        referer: Optional[str],
        pwd: Optional[str] = None,
    ) -> RedirectResult:
        limited = await check_rate_limit(f"ratelimit:redirect:{short_code}:{ip}", capacity=100, refill_rate_per_sec=1.67)
        if limited:
            raise RateLimitError()

        url_data = await self._fetch_url(short_code)
        self._validate(url_data)
        self._check_password(url_data, pwd)
        destination = self._apply_deep_link(url_data, user_agent)
        await self._handle_one_time(url_data)

        await self.events.dispatch("url-clicked", {
            "event_id": None,
            "short_code": short_code,
            "original_url": destination,
            "workspace_id": url_data["workspace_id"],
            "ip_address": ip,
            "user_agent": user_agent,
            "referer": referer,
            "clicked_at": datetime.utcnow().isoformat(),
        }, key=short_code)

        return RedirectResult(
            destination=destination,
            url_id=url_data["id"],
            short_code=short_code,
            workspace_id=url_data["workspace_id"],
            is_one_time=url_data.get("is_one_time", False),
        )

    async def _fetch_url(self, short_code: str) -> dict:
        url_data = await get_url_cache(short_code)
        if url_data:
            return url_data
        url_obj = await self.url_repo.get_by_short_code(short_code)
        if not url_obj:
            raise URLNotFound()
        url_data = {
            "id": url_obj.id,
            "short_code": url_obj.short_code,
            "original_url": url_obj.original_url,
            "workspace_id": url_obj.workspace_id,
            "is_ab_test": url_obj.is_ab_test,
            "is_one_time": url_obj.is_one_time,
            "ios_url": url_obj.ios_url,
            "android_url": url_obj.android_url,
            "password_hash": url_obj.password_hash,
            "status": url_obj.status.value,
            "expires_at": url_obj.expires_at.isoformat() if url_obj.expires_at else None,
        }
        await set_url_cache(short_code, url_data)
        return url_data

    def _validate(self, url_data: dict):
        if url_data["status"] == "disabled":
            raise URLDisabled()
        if url_data["expires_at"]:
            expires_at = datetime.fromisoformat(url_data["expires_at"])
            if expires_at < datetime.utcnow():
                raise URLExpired()

    def _check_password(self, url_data: dict, pwd: Optional[str]):
        if url_data["password_hash"]:
            if not pwd or not verify_password(pwd, url_data["password_hash"]):
                raise URLPasswordIncorrect()

    def _apply_deep_link(self, url_data: dict, user_agent: Optional[str]) -> str:
        dest = url_data["original_url"]
        if user_agent:
            ua = user_agent.lower()
            if any(d in ua for d in ["iphone", "ipad", "ipod"]) and url_data["ios_url"]:
                dest = url_data["ios_url"]
            elif "android" in ua and url_data["android_url"]:
                dest = url_data["android_url"]
        return dest

    async def _handle_one_time(self, url_data: dict):
        if url_data.get("is_one_time"):
            await self.url_repo.soft_delete(url_data["id"])
            await delete_url_cache(url_data["short_code"])
