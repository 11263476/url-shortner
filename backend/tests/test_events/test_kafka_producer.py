from unittest.mock import AsyncMock, patch

import pytest

from src.events.kafka import publish_event, publish_raw


class TestKafkaProducer:
    @pytest.mark.asyncio
    async def test_publish_event_calls_serialize_and_send(self):
        mock_producer = AsyncMock()

        with patch("src.events.kafka.producer", mock_producer), \
             patch("src.events.kafka.serialize", return_value=b"serialized-avro-bytes"):
            await publish_event("url-created", {"short_code": "test"})
            mock_producer.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_event_with_key(self):
        mock_producer = AsyncMock()

        with patch("src.events.kafka.producer", mock_producer), \
             patch("src.events.kafka.serialize", return_value=b"serialized-avro-bytes"):
            await publish_event("url-created", {"short_code": "test"}, key="test-key")
            mock_producer.send_and_wait.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_raw_sends_bytes(self):
        mock_producer = AsyncMock()

        with patch("src.events.kafka.producer", mock_producer):
            await publish_raw("dlq-url-clicked", b"raw-bytes")
            mock_producer.send_and_wait.assert_called_once_with(
                "dlq-url-clicked", value=b"raw-bytes", key=None
            )

    @pytest.mark.asyncio
    async def test_publish_event_no_producer_returns_gracefully(self):
        with patch("src.events.kafka.producer", None):
            result = await publish_event("url-created", {"short_code": "test"})
            assert result is None

    @pytest.mark.asyncio
    async def test_publish_raw_no_producer_returns_gracefully(self):
        with patch("src.events.kafka.producer", None):
            result = await publish_raw("some-topic", b"data")
            assert result is None
