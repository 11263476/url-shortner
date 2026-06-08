import asyncio, json, ssl
from aiokafka import AIOKafkaConsumer
from user_agents import parse
from datetime import datetime

from src.logging import setup_logging, get_logger
from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.repositories import URLRepository, AnalyticsRepository
from src.documents.click_event import ClickEvent


async def consume_url_clicked_events():
    setup_logging()
    logger = get_logger("analytics-worker")

    kwargs = {
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "security_protocol": settings.KAFKA_SECURITY_PROTOCOL,
        "group_id": "analytics-worker-group",
        "auto_offset_reset": "earliest",
        "enable_auto_commit": False,
    }

    if settings.KAFKA_SASL_USERNAME:
        kwargs["sasl_mechanism"] = settings.KAFKA_SASL_MECHANISM
        kwargs["sasl_plain_username"] = settings.KAFKA_SASL_USERNAME
        kwargs["sasl_plain_password"] = settings.KAFKA_SASL_PASSWORD

    if settings.KAFKA_SSL_CA_PATH:
        context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CA_PATH)
        kwargs["ssl_context"] = context

    consumer = AIOKafkaConsumer("url-clicked", **kwargs)
    await consumer.start()
    logger.info("Analytics Worker listening on 'url-clicked'...")

    try:
        async for msg in consumer:
            try:
                event_data = json.loads(msg.value.decode("utf-8"))
                await process_event(event_data, logger)
                await consumer.commit()
            except Exception as e:
                logger.warning("Error processing event at offset %s: %s", msg.offset, str(e))
    finally:
        await consumer.stop()


async def process_event(event_data: dict, logger):
    ua_string = event_data.get("user_agent")
    browser = os = device = None
    if ua_string:
        user_agent = parse(ua_string)
        browser = user_agent.browser.family
        os = user_agent.os.family
        device = user_agent.device.family

    click_event = ClickEvent(
        event_id=event_data.get("event_id"),
        short_code=event_data["short_code"],
        original_url=event_data["original_url"],
        workspace_id=event_data["workspace_id"],
        ip_address=event_data["ip_address"],
        user_agent=ua_string,
        referer=event_data.get("referer"),
        browser=browser, os=os, device=device,
        clicked_at=datetime.fromisoformat(event_data["clicked_at"]),
    )

    try:
        await click_event.insert()
    except Exception as e:
        if "duplicate key error" in str(e).lower():
            logger.info("Duplicate event_id %s ignored.", click_event.event_id)
            return
        raise

    async with AsyncSessionLocal() as db:
        url_repo = URLRepository(db)
        analytics_repo = AnalyticsRepository(db)
        url_id = await url_repo.get_url_id_by_short_code(event_data["short_code"])
        if not url_id:
            logger.warning("URL not found for short_code: %s", event_data["short_code"])
            return
        await analytics_repo.upsert_click(url_id, click_event.clicked_at)


if __name__ == "__main__":
    asyncio.run(consume_url_clicked_events())
