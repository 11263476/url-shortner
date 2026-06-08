import asyncio, signal
from datetime import datetime
from sqlalchemy import select

from src.logging import setup_logging, get_logger
from src.core.database import AsyncSessionLocal
from src.models.url import URL, URLStatus
from src.repositories import URLRepository
from src.core.redis import delete_url_cache


async def scan_and_expire_urls(logger):
    async with AsyncSessionLocal() as db:
        url_repo = URLRepository(db)
        result = await db.execute(
            select(URL).where(
                URL.status == URLStatus.active,
                URL.expires_at.isnot(None),
                URL.expires_at < datetime.utcnow(),
            )
        )
        expired_urls = result.scalars().all()

        if not expired_urls:
            return

        logger.info("Found %d expired URLs to process.", len(expired_urls))
        for url in expired_urls:
            await url_repo.update(url.id, status=URLStatus.disabled)
            await delete_url_cache(url.short_code)
            logger.info("Expired URL: %s (evicted from cache)", url.short_code)


async def start_worker():
    setup_logging()
    logger = get_logger("expiry-worker")
    logger.info("Expiry Worker started")
    interval = 30
    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    while not stop.is_set():
        try:
            await scan_and_expire_urls(logger)
        except Exception as e:
            logger.warning("Error in expiry loop: %s", str(e))
        await asyncio.sleep(interval)

    logger.info("Expiry Worker stopped")


if __name__ == "__main__":
    asyncio.run(start_worker())
