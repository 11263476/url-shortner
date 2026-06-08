import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis
from aiokafka import AIOKafkaProducer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Add backend/src to path
sys.path.insert(0, r"c:\Users\ramat\Desktop\project\url-shortner\backend")
from src.core.config import settings

async def test_postgres():
    print("Testing PostgreSQL Connection...")
    try:
        engine = create_async_engine(settings.ASYNC_DATABASE_URI)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            val = result.scalar()
            print(f"[OK] PostgreSQL connection successful. Result: {val}")
        await engine.dispose()
    except Exception as e:
        print(f"[FAIL] PostgreSQL connection failed: {e}")

async def test_mongodb():
    print("Testing MongoDB Connection...")
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.MONGODB_DB]
        res = await db.command("ping")
        print(f"[OK] MongoDB connection successful. Result: {res}")
    except Exception as e:
        print(f"[FAIL] MongoDB connection failed: {e}")

async def test_redis():
    print("Testing Redis Connection...")
    try:
        redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        res = await redis.ping()
        print(f"[OK] Redis connection successful. Result: {res}")
        await redis.aclose()
    except Exception as e:
        print(f"[FAIL] Redis connection failed: {e}")

async def test_kafka():
    print("Testing Kafka Connection...")
    try:
        kwargs = {
            "bootstrap_servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "security_protocol": settings.KAFKA_SECURITY_PROTOCOL,
        }
        if settings.KAFKA_SASL_USERNAME:
            kwargs["sasl_mechanism"] = settings.KAFKA_SASL_MECHANISM
            kwargs["sasl_plain_username"] = settings.KAFKA_SASL_USERNAME
            kwargs["sasl_plain_password"] = settings.KAFKA_SASL_PASSWORD
        
        if settings.KAFKA_SSL_CA_PATH:
            import ssl
            # Map ssl context
            context = ssl.create_default_context(cafile=settings.KAFKA_SSL_CA_PATH)
            kwargs["ssl_context"] = context
            
        print(f"Kafka configuration: {kwargs}")
        producer = AIOKafkaProducer(**kwargs)
        await producer.start()
        print("[OK] Kafka connection successful.")
        await producer.stop()
    except Exception as e:
        print(f"[FAIL] Kafka connection failed: {e}")

async def main():
    await test_postgres()
    await test_mongodb()
    await test_redis()
    await test_kafka()

if __name__ == "__main__":
    asyncio.run(main())
