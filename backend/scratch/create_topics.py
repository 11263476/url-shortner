import asyncio
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from src.core.config import settings
import ssl

async def create_topics():
    print("[INFO] Creating Kafka topics...")
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
        kwargs["ssl_context"] = context

    admin_client = AIOKafkaAdminClient(**kwargs)
    await admin_client.start()
    
    topics = [
        NewTopic(name="url-clicked", num_partitions=1, replication_factor=1),
        NewTopic(name="url-created", num_partitions=1, replication_factor=1)
    ]
    
    try:
        await admin_client.create_topics(new_topics=topics)
        print("[OK] Topics created successfully")
    except Exception as e:
        print(f"[WARNING] Could not create topics: {e}")
    finally:
        await admin_client.close()

if __name__ == "__main__":
    asyncio.run(create_topics())
