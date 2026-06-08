from abc import ABC, abstractmethod
from typing import Optional


class EventDispatcher(ABC):
    @abstractmethod
    async def dispatch(self, topic: str, value: dict, key: Optional[str] = None) -> None:
        ...


class KafkaEventDispatcher(EventDispatcher):
    async def dispatch(self, topic: str, value: dict, key: Optional[str] = None) -> None:
        from src.events.kafka import publish_event
        try:
            await publish_event(topic, value, key=key)
        except Exception as e:
            print(f"[WARNING] Failed to publish event to {topic}: {e}")


class NullEventDispatcher(EventDispatcher):
    async def dispatch(self, topic: str, value: dict, key: Optional[str] = None) -> None:
        pass
