import asyncio
import logging
import weakref
from typing import Optional

import async_timeout

log = logging.getLogger(__name__)

_PATCHED = False


def apply_sni_patch(bootstrap_hostname: Optional[str] = None):
    global _PATCHED
    if _PATCHED:
        return
    _PATCHED = True

    if not bootstrap_hostname:
        log.warning("No bootstrap hostname provided, SNI patch skipped")
        return

    # Strip port if present
    sni_hostname = bootstrap_hostname.split(":")[0]

    from aiokafka.conn import READER_LIMIT, AIOKafkaConnection, AIOKafkaProtocol

    original_connect = AIOKafkaConnection.connect

    async def patched_connect(self):
        loop = asyncio.get_running_loop()
        self._closed_fut = loop.create_future()

        if self._security_protocol in ("PLAINTEXT", "SASL_PLAINTEXT"):
            ssl = None
        else:
            ssl = self._ssl_context

        reader = asyncio.StreamReader(limit=READER_LIMIT)
        protocol = AIOKafkaProtocol(self._closed_fut, reader, loop=loop)
        async with async_timeout.timeout(self._request_timeout):
            transport, _ = await loop.create_connection(
                lambda: protocol,
                self._host,
                self._port,
                ssl=ssl,
                server_hostname=sni_hostname if ssl else None,
            )
        writer = asyncio.StreamWriter(transport, protocol, reader, loop)
        self._reader, self._writer, self._protocol = reader, writer, protocol

        self._read_task = self._create_reader_task()
        if self._max_idle_ms is not None:
            self._idle_handle = loop.call_soon(
                AIOKafkaConnection._idle_check, weakref.ref(self)
            )

        try:
            await self._do_version_lookup()
            if self._security_protocol in ("SASL_SSL", "SASL_PLAINTEXT"):
                await self._do_sasl_handshake()
        except BaseException:
            self.close()
            raise

        return reader, writer

    AIOKafkaConnection.connect = patched_connect
    log.info("Applied SNI patch: will use '%s' for all TLS connections", sni_hostname)
