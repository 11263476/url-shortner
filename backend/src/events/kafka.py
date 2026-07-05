import asyncio
import ssl
from typing import Optional

from aiokafka import AIOKafkaProducer

from src.core.config import settings
from src.events.schemas import serialize
from src.workers._sni_patch import apply_sni_patch

producer: Optional[AIOKafkaProducer] = None

async def init_kafka():
    global producer
    apply_sni_patch(settings.KAFKA_BOOTSTRAP_SERVERS)
    kwargs = {
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "security_protocol": settings.KAFKA_SECURITY_PROTOCOL,
    }
    if settings.KAFKA_SASL_USERNAME:
        kwargs["sasl_mechanism"] = settings.KAFKA_SASL_MECHANISM
        kwargs["sasl_plain_username"] = settings.KAFKA_SASL_USERNAME
        kwargs["sasl_plain_password"] = settings.KAFKA_SASL_PASSWORD
    if settings.KAFKA_SSL_CA_PATH:
        context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CA_PATH)
        context.check_hostname = False
        kwargs["ssl_context"] = context
    producer = AIOKafkaProducer(**kwargs)
    await producer.start()
    print("[OK] Kafka Producer started successfully.")

async def close_kafka():
    global producer
    if producer:
        await producer.stop()
        print("[OK] Kafka Producer stopped.")

async def _send_background(topic, value, key):
    try:
        await producer.send_and_wait(topic, value=value, key=key)
    except Exception as e:
        print(f"[WARNING] Failed to publish event to {topic}: {e}")

async def publish_event(topic: str, value: dict, key: Optional[str] = None):
    global producer
    if not producer:
        return
    payload = serialize(topic, value)
    encoded_key = key.encode("utf-8") if key else None
    asyncio.create_task(_send_background(topic, payload, encoded_key))


async def publish_raw(topic: str, value: bytes, key: Optional[bytes] = None):
    global producer
    if not producer:
        return
    asyncio.create_task(_send_background(topic, value, key))
