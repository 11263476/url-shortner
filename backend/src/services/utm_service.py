"""UTM parameter parsing utility."""
from urllib.parse import parse_qs, urlparse


def parse_utm(url: str) -> dict:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return {
        "utm_source": (params.get("utm_source") or [None])[0],
        "utm_medium": (params.get("utm_medium") or [None])[0],
        "utm_campaign": (params.get("utm_campaign") or [None])[0],
    }
