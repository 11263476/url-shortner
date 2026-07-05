import io
import json
import os
from pathlib import Path

import fastavro
import httpx

from src.core.config import settings

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas" / "avro"

_schemas: dict[str, dict] = {}


def _load_schema(topic: str) -> dict:
    if topic not in _schemas:
        path = SCHEMA_DIR / f"{topic}.avsc"
        if not path.exists():
            raise FileNotFoundError(f"Avro schema not found: {path}")
        with open(path) as f:
            _schemas[topic] = json.load(f)
    return _schemas[topic]


def serialize(topic: str, value: dict) -> bytes:
    schema = _load_schema(topic)
    buf = io.BytesIO()
    fastavro.schemaless_writer(buf, schema, value)
    return buf.getvalue()


def deserialize(topic: str, data: bytes) -> dict:
    schema = _load_schema(topic)
    buf = io.BytesIO(data)
    try:
        return fastavro.schemaless_reader(buf, schema)
    except Exception:
        # Schema may have evolved (new fields with defaults).
        # Try reading with a schema that drops fields that have defaults
        # (old messages written before the schema was extended).
        old_schema = _evolve_schema(schema)
        buf.seek(0)
        return fastavro.schemaless_reader(buf, old_schema)


def _evolve_schema(schema: dict) -> dict:
    """Return a version of the schema with only required fields (no defaults)."""
    fields = []
    for f in schema["fields"]:
        if "default" not in f:
            fields.append(f)
    return {**schema, "fields": fields}


async def register_schemas():
    url = getattr(settings, "SCHEMA_REGISTRY_URL", None) or os.getenv("SCHEMA_REGISTRY_URL")
    if not url:
        return

    for topic in ("url-created", "url-clicked"):
        schema = _load_schema(topic)
        payload = {
            "schema": json.dumps(schema),
            "schemaType": "AVRO",
        }
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{url}/subjects/{topic}-value/versions",
                    json=payload,
                    timeout=10,
                )
                if resp.is_success:
                    print(f"[OK] Registered schema for {topic}")
                else:
                    print(f"[WARN] Schema registration for {topic}: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[WARN] Could not reach schema registry at {url}: {e}")


def get_schema(topic: str) -> dict:
    return _load_schema(topic)
