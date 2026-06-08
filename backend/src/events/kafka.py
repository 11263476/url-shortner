import ssl
import json
from aiokafka import AIOKafkaProducer
from src.core.config import settings
from typing import Optional

producer: Optional[AIOKafkaProducer] = None

async def init_kafka():
    """Initialize AIOKafkaProducer on application startup."""
    global producer
    
    kwargs = {
        "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
        "security_protocol": settings.KAFKA_SECURITY_PROTOCOL,
    }
    
    if settings.KAFKA_SASL_USERNAME:
        kwargs["sasl_mechanism"] = settings.KAFKA_SASL_MECHANISM
        kwargs["sasl_plain_username"] = settings.KAFKA_SASL_USERNAME
        kwargs["sasl_plain_password"] = settings.KAFKA_SASL_PASSWORD
        
    if settings.KAFKA_SSL_CA_PATH:
        # Load CA certificate for secure SSL verification (required for Aiven Kafka)
        context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CA_PATH)
        kwargs["ssl_context"] = context
        
    producer = AIOKafkaProducer(**kwargs)
    await producer.start()
    print("[OK] Kafka Producer started successfully.")

async def close_kafka():
    """Close AIOKafkaProducer on application shutdown."""
    global producer
    if producer:
        await producer.stop()
        print("[OK] Kafka Producer stopped.")

async def publish_event(topic: str, value: dict, key: Optional[str] = None):
    """Publish a serialized JSON event to a Kafka topic."""
    global producer
    if not producer:
        print(f"[WARNING] Kafka Producer not initialized. Skipping event to {topic}.")
        return
    
    payload = json.dumps(value).encode("utf-8")
    encoded_key = key.encode("utf-8") if key else None
    
    await producer.send_and_wait(topic, value=payload, key=encoded_key)
