"""Loki log handler — pushes JSON log records to Grafana Loki via HTTP with batching."""
import json
import logging
import queue
import threading
import time
from datetime import datetime, timezone

import httpx

from src.core.config import settings


class BatchedLokiHandler(logging.Handler):
    """Batched Loki handler using background worker thread."""

    def __init__(self, batch_size: int = 10, flush_interval: float = 5.0):
        super().__init__()
        self.loki_url = settings.LOKI_URL.rstrip("/") + "/loki/api/v1/push"
        auth = None
        if settings.LOKI_USERNAME and settings.LOKI_PASSWORD:
            auth = (settings.LOKI_USERNAME, settings.LOKI_PASSWORD)
        self._client = httpx.Client(timeout=5.0, auth=auth)
        self._queue: queue.Queue = queue.Queue(maxsize=1000)
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._shutdown = False
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _worker_loop(self):
        batch = []
        last_flush = time.time()
        while not self._shutdown:
            try:
                record = self._queue.get(timeout=0.5)
                if record is None:  # Shutdown signal
                    break
                batch.append(record)
            except queue.Empty:
                pass

            now = time.time()
            if batch and (len(batch) >= self._batch_size or now - last_flush >= self._flush_interval):
                self._flush_batch(batch)
                batch.clear()
                last_flush = now

        # Flush remaining on shutdown
        if batch:
            self._flush_batch(batch)

    def _flush_batch(self, batch):
        if not batch:
            return
        try:
            streams = {}
            for record in batch:
                log_entry = self.format(record)
                if isinstance(log_entry, str):
                    try:
                        log_entry = json.loads(log_entry)
                    except json.JSONDecodeError:
                        log_entry = {"message": log_entry}  # type: ignore[assignment]

                timestamp_ns = int(datetime.now(timezone.utc).timestamp() * 1e9)
                level = record.levelname.lower()
                stream_key = (settings.PROJECT_NAME, settings.ENVIRONMENT, level)
                if stream_key not in streams:
                    streams[stream_key] = {
                        "stream": {
                            "service": settings.PROJECT_NAME,
                            "environment": settings.ENVIRONMENT,
                            "level": level,
                        },
                        "values": [],
                    }
                streams[stream_key]["values"].append([str(timestamp_ns), json.dumps(log_entry)])  # type: ignore[attr-defined]

            payload = {"streams": list(streams.values())}
            self._client.post(self.loki_url, json=payload)
        except Exception:
            pass  # Silently drop on failure; logs go to stdout

    def emit(self, record: logging.LogRecord):
        if not settings.LOKI_ENABLED:
            return
        try:
            self._queue.put_nowait(record)
        except queue.Full:
            pass  # Drop if queue full (backpressure)

    def close(self):
        self._shutdown = True
        self._queue.put(None)  # Signal worker to exit
        self._worker.join(timeout=5.0)
        self._client.close()
        super().close()
