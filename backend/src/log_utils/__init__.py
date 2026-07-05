"""
Structured logging setup with JSON format and correlation ID support.
Integrates with Loki for centralized log aggregation.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from pythonjsonlogger import jsonlogger

from src.core.config import settings


class CorrelationIdFilter(logging.Filter):
    def __init__(self, correlation_id: Optional[str] = None):
        super().__init__()
        self.correlation_id = correlation_id

    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = self.correlation_id or "no-correlation-id"
        return True


class JSONFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)
        log_record['timestamp'] = datetime.utcnow().isoformat() + "Z"
        log_record['service'] = settings.PROJECT_NAME
        log_record['environment'] = settings.ENVIRONMENT
        log_record['version'] = "1.0.0"
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id
        for attr in ('trace_id', 'span_id', 'user_id', 'workspace_id', 'url_id'):
            if hasattr(record, attr):
                log_record[attr] = getattr(record, attr)


def setup_logging(correlation_id: Optional[str] = None):
    logger = logging.getLogger("url-shortener")
    is_prod = settings.ENVIRONMENT == "production"
    log_level = logging.INFO if is_prod else logging.DEBUG
    logger.setLevel(log_level)
    logger.handlers.clear()
    formatter = JSONFormatter(fmt='%(timestamp)s %(level)s %(name)s %(message)s', timestamp=True)
    correlation_filter = CorrelationIdFilter(correlation_id)

    # Drop DEBUG in production
    if is_prod:
        class ProdFilter(logging.Filter):
            def filter(self, record):
                return record.levelno >= logging.INFO
        correlation_filter = ProdFilter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(correlation_filter)
    logger.addHandler(console_handler)

    log_dir = Path(os.getenv("LOG_DIR", "logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{logger.name.replace('url-shortener.', '')}.log"
    file_handler = logging.FileHandler(filename=log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(correlation_filter)
    logger.addHandler(file_handler)

    if settings.LOKI_ENABLED and settings.LOKI_URL:
        try:
            from src.log_utils.loki_handler import BatchedLokiHandler
            loki_handler = BatchedLokiHandler(batch_size=10, flush_interval=5.0)
            loki_handler.setLevel(logging.INFO)
            loki_handler.setFormatter(formatter)
            loki_handler.addFilter(correlation_filter)
            logger.addHandler(loki_handler)
        except Exception as e:
            print(f"[LOGGING] Loki handler not available: {e}")

    logger.addFilter(correlation_filter)
    return logger


def get_logger(name: str = "url-shortener") -> logging.Logger:
    if name != "url-shortener" and not name.startswith("url-shortener."):
        name = f"url-shortener.{name}"
    return logging.getLogger(name)


def log_request_start(logger: logging.Logger, method: str, path: str, correlation_id: str):
    logger.info(
        f"Request started: {method} {path}",
        extra={"correlation_id": correlation_id, "event": "request_start", "http_method": method, "http_path": path}
    )


def log_request_end(logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float, correlation_id: str):
    logger.info(
        f"Request completed: {method} {path} \u2192 {status_code} ({duration_ms:.2f}ms)",
        extra={"correlation_id": correlation_id, "event": "request_end", "http_method": method, "http_path": path, "http_status_code": status_code, "duration_ms": duration_ms}
    )


__all__ = ["setup_logging", "get_logger", "log_request_start", "log_request_end"]
