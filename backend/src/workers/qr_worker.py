import asyncio, json, ssl, io, base64, qrcode
from aiokafka import AIOKafkaConsumer

from src.logging import setup_logging, get_logger
from src.core.config import settings
from src.core.database import AsyncSessionLocal
from src.repositories import URLRepository


def generate_qr_base64(url: str) -> str:
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


async def process_url_created_event(event_data: dict, logger):
    short_code = event_data.get("short_code")
    original_url = event_data.get("original_url")

    if not short_code or not original_url:
        logger.warning("Missing short_code or original_url in event")
        return

    base_url = event_data.get("base_url", settings.FRONTEND_URL or "http://localhost:8000")
    redirect_url = f"{base_url}/{short_code}"
    logger.info("Generating QR code for: %s", redirect_url)

    try:
        qr_base64 = generate_qr_base64(redirect_url)
    except Exception as e:
        logger.error("Failed to generate QR code for %s: %s", short_code, str(e))
        return

    async with AsyncSessionLocal() as db:
        url_repo = URLRepository(db)
        url = await url_repo.get_by_short_code(short_code)
        if url:
            await url_repo.update(url.id, qr_code=qr_base64)
            logger.info("QR code stored for short_code: %s (%d bytes)", short_code, len(qr_base64))


async def consume_url_created_events():
    setup_logging()
    logger = get_logger("qr-worker")

    kwargs = {
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "security_protocol": settings.KAFKA_SECURITY_PROTOCOL,
        "group_id": "qr-worker-group",
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

    consumer = AIOKafkaConsumer("url-created", **kwargs)
    await consumer.start()
    logger.info("QR Worker listening on 'url-created'...")

    try:
        async for msg in consumer:
            try:
                event_data = json.loads(msg.value.decode("utf-8"))
                await process_url_created_event(event_data, logger)
                await consumer.commit()
            except Exception as e:
                logger.warning("Error processing QR event at offset %s: %s", msg.offset, str(e))
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(consume_url_created_events())
