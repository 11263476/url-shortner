from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings
from src.documents.click_event import ClickEvent

async def init_mongodb():
    """Initialize Beanie ODM with Motor async client."""
    client = AsyncIOMotorClient(settings.MONGODB_URI)
    await init_beanie(
        database=client[settings.MONGODB_DB],
        document_models=[ClickEvent],
    )
