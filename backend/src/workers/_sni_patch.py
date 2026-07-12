import logging
import ssl
from typing import Optional, Union


class SNIAwareSSLContext(ssl.SSLContext):
    """SSLContext subclass that injects ``server_hostname`` into every
    ``wrap_socket`` call so that TLS handshakes include the correct SNI
    extension.

    aiokafka's internal connection machinery calls ``wrap_socket`` without
    *server_hostname* when the broker address is an IP instead of a DNS name.
    Some Kafka providers (e.g. Aiven) rely on SNI for TLS routing, so we
    always pass the original bootstrap hostname through this subclass.
    """

    def __init__(self, protocol: int = ssl.PROTOCOL_TLS_CLIENT, *, sni_hostname: Optional[str] = None) -> None:
        super().__init__(protocol)  # type: ignore[call-arg]
        self._sni_hostname = sni_hostname

    def wrap_socket(self, sock, server_side: bool = False,
                    do_handshake_on_connect: bool = True,
                    suppress_ragged_eofs: bool = True,
                    server_hostname: Optional[Union[str, bytes]] = None,
                    session: Optional[ssl.SSLSession] = None):
        if server_hostname is None and self._sni_hostname:
            server_hostname = self._sni_hostname
        return super().wrap_socket(
            sock, server_side, do_handshake_on_connect,
            suppress_ragged_eofs, server_hostname, session,
        )


def _extract_hostname(bootstrap_servers: str) -> Optional[str]:
    hostname = bootstrap_servers.split(":")[0]
    return hostname if hostname else None


def _make_sni_context(bootstrap_servers: str, cafile: str) -> ssl.SSLContext:
    """Build an SSL context that sends the correct SNI hostname.

    Replaces the old pattern of ``ssl.create_default_context()`` +
    ``apply_sni_patch()`` with a single ``SNIAwareSSLContext``.
    """
    sni_hostname = _extract_hostname(bootstrap_servers)
    ctx: SNIAwareSSLContext = SNIAwareSSLContext(sni_hostname=sni_hostname)
    ctx.load_verify_locations(cafile=cafile)
    ctx.check_hostname = False
    return ctx


# ---------------------------------------------------------------------------
# Backward-compatible no-op — the SNI is now handled by SNIAwareSSLContext
# directly, so calling apply_sni_patch is no longer necessary.
# ---------------------------------------------------------------------------
_PATCHED = False


def apply_sni_patch(bootstrap_hostname: Optional[str] = None) -> None:
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True
    log = logging.getLogger(__name__)
    log.info("SNI patch is no longer required — SNIAwareSSLContext handles TLS.")
    return
