import asyncio, signal, json, httpx, hmac, hashlib
from sqlalchemy import select

from src.logging import setup_logging, get_logger
from src.core.database import AsyncSessionLocal
from src.models.webhook import Webhook
from src.models.webhook_event import WebhookEvent
from src.services.webhook_service import decrypt_secret


async def retry_failed_events(logger):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(WebhookEvent).where(
                WebhookEvent.status == "failed",
                WebhookEvent.retry_count < 3,
            )
        )
        failed_events = result.scalars().all()

        if not failed_events:
            return

        logger.info("Found %d failed events to retry.", len(failed_events))

        for event in failed_events:
            wh = await db.get(Webhook, event.webhook_id)
            if not wh or not wh.is_active:
                continue

            payload = json.loads(event.payload)
            secret = decrypt_secret(wh.secret)
            payload_bytes = event.payload.encode()
            signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        wh.url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "X-Webhook-Signature": signature,
                            "X-Webhook-Event": event.event_type,
                        },
                        timeout=10.0,
                    )
                event.status = "delivered"
                event.response_code = resp.status_code
                event.error = None
            except Exception as e:
                event.retry_count += 1
                event.error = str(e)

        await db.commit()
        logger.info("Webhook retry scan complete.")


async def start_worker():
    setup_logging()
    logger = get_logger("webhook-retry-worker")
    logger.info("Webhook Retry Worker started")
    interval = 120
    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass

    while not stop.is_set():
        try:
            await retry_failed_events(logger)
        except Exception as e:
            logger.warning("Error in webhook retry loop: %s", str(e))
        await asyncio.sleep(interval)

    logger.info("Webhook Retry Worker stopped")


if __name__ == "__main__":
    asyncio.run(start_worker())
