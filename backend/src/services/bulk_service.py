import csv
import io
import zipfile
import json
import qrcode
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.url_repository import URLRepository
from src.repositories.workspace_repository import WorkspaceRepository
from src.core.redis import delete_url_cache
from src.utils.base62 import generate_short_code
from src.models.url import URL, URLStatus
from src.errors import WorkspaceNotFound, BadRequestError, NotFoundError


class BulkService:
    def __init__(self, db: AsyncSession, url_repo: URLRepository, workspace_repo: WorkspaceRepository):
        self.db = db
        self.url_repo = url_repo
        self.workspace_repo = workspace_repo

    async def _verify_workspace(self, workspace_id: int, user_id: int):
        ws = await self.workspace_repo.verify_access(workspace_id, user_id)
        if not ws:
            raise WorkspaceNotFound()

    async def create_from_csv(self, workspace_id: int, user_id: int, contents: bytes):
        await self._verify_workspace(workspace_id, user_id)
        try:
            reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))
        except Exception:
            raise BadRequestError("Invalid CSV file.")
        created, errors = [], []
        for i, row in enumerate(reader, start=2):
            original_url = row.get("original_url", "").strip()
            if not original_url:
                errors.append({"row": i, "error": "Missing original_url"})
                continue
            custom_alias = row.get("custom_alias", "").strip() or None
            short_code = custom_alias
            if not short_code:
                for _ in range(5):
                    candidate = generate_short_code()
                    if not await self.url_repo.alias_exists(candidate):
                        short_code = candidate
                        break
            if not short_code:
                errors.append({"row": i, "error": "Could not generate unique short code"})
                continue
            url = URL(short_code=short_code, original_url=original_url, user_id=user_id, workspace_id=workspace_id, custom_alias=custom_alias, status=URLStatus.active)
            self.db.add(url)
            created.append(short_code)
        await self.db.commit()
        return {"created": len(created), "errors": errors, "short_codes": created}

    async def update(self, workspace_id: int, user_id: int, url_ids: list[int], **kwargs):
        await self._verify_workspace(workspace_id, user_id)
        if not kwargs:
            raise BadRequestError("No update fields provided.")
        await self.url_repo.bulk_update(url_ids, workspace_id, **kwargs)

    async def disable(self, workspace_id: int, user_id: int, url_ids: list[int]):
        await self._verify_workspace(workspace_id, user_id)
        rows = await self.url_repo.get_short_codes_by_ids(url_ids, workspace_id)
        await self.url_repo.bulk_update(url_ids, workspace_id, status=URLStatus.disabled)
        for row in rows:
            await delete_url_cache(row.short_code)
        return len(rows)

    async def reactivate(self, workspace_id: int, user_id: int, url_ids: list[int]):
        from sqlalchemy import update, and_
        await self._verify_workspace(workspace_id, user_id)
        await self.db.execute(
            update(URL)
            .where(and_(URL.id.in_(url_ids), URL.workspace_id == workspace_id, URL.status == URLStatus.disabled))
            .values(status=URLStatus.active)
        )
        await self.db.commit()
        return len(url_ids)

    async def delete(self, workspace_id: int, user_id: int, url_ids: list[int]):
        await self._verify_workspace(workspace_id, user_id)
        rows = await self.url_repo.get_short_codes_by_ids(url_ids, workspace_id)
        await self.url_repo.bulk_update(url_ids, workspace_id, status=URLStatus.deleted)
        for row in rows:
            await delete_url_cache(row.short_code)
        return len(rows)

    async def export(self, workspace_id: int, user_id: int, fmt: str):
        await self._verify_workspace(workspace_id, user_id)
        urls = await self.url_repo.get_workspace_urls(workspace_id)
        data = [
            {
                "id": u.id, "short_code": u.short_code, "original_url": u.original_url,
                "custom_alias": u.custom_alias or "",
                "expires_at": u.expires_at.isoformat() if u.expires_at else "",
                "created_at": u.created_at.isoformat(),
            }
            for u in urls
        ]
        if fmt == "json":
            return json.dumps(data, indent=2), "application/json", "urls_export.json"
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["id", "short_code", "original_url", "custom_alias", "expires_at", "created_at"])
        writer.writeheader()
        for d in data:
            writer.writerow(d)
        output.seek(0)
        return output.read(), "text/csv", "urls_export.csv"

    async def generate_qr_zip(self, workspace_id: int, user_id: int, url_ids: list[int] | None):
        await self._verify_workspace(workspace_id, user_id)
        urls = await self.url_repo.get_workspace_urls(workspace_id)
        if url_ids:
            urls = [u for u in urls if u.id in url_ids]
        if not urls:
            raise NotFoundError("No URLs found for QR generation.")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for u in urls:
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(f"http://localhost:8000/{u.short_code}")
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                buf.seek(0)
                zf.writestr(f"{u.short_code}.png", buf.read())
        zip_buffer.seek(0)
        return zip_buffer
