"""Local TCP client for the Felicity WiFi stick.

Protocol (observed, same transport as the Felicity battery stick):
- Plain TCP to port 53970 on the stick.
- Client sends an ASCII command, e.g. ``wifilocalMonitor:get dev real infor``.
- Stick answers with a single JSON object; the payload ends at the first ``}``
  that closes the top-level object.
- Client acknowledges with a single ``.`` byte.

The stick only handles one client at a time, so every poll opens a fresh
connection and closes it again.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from .const import ACK, CONNECT_TIMEOUT, QUERY_DATE, QUERY_REALTIME, READ_TIMEOUT


class FelicityError(Exception):
    """Base error."""


class FelicityConnectionError(FelicityError):
    """Stick not reachable or connection dropped."""


class FelicityProtocolError(FelicityError):
    """Stick answered with something we cannot parse."""


def _extract_object(buffer: bytes) -> bytes | None:
    """Return the first complete top-level JSON object in buffer, or None."""
    depth = 0
    start = buffer.find(b"{")
    if start < 0:
        return None
    in_string = False
    escape = False
    for idx in range(start, len(buffer)):
        char = buffer[idx : idx + 1]
        if in_string:
            if escape:
                escape = False
            elif char == b"\\":
                escape = True
            elif char == b'"':
                in_string = False
            continue
        if char == b'"':
            in_string = True
        elif char == b"{":
            depth += 1
        elif char == b"}":
            depth -= 1
            if depth == 0:
                return buffer[start : idx + 1]
    return None


class FelicityClient:
    """Minimal async client."""

    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self._lock = asyncio.Lock()

    async def _query(self, command: bytes) -> dict[str, Any]:
        async with self._lock:
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), CONNECT_TIMEOUT
                )
            except (TimeoutError, OSError) as err:
                raise FelicityConnectionError(
                    f"Cannot connect to {self.host}:{self.port}: {err}"
                ) from err

            try:
                writer.write(command)
                await writer.drain()

                buffer = b""
                payload: bytes | None = None
                loop = asyncio.get_running_loop()
                deadline = loop.time() + READ_TIMEOUT
                while payload is None:
                    remaining = deadline - loop.time()
                    if remaining <= 0:
                        raise FelicityConnectionError(
                            f"Timeout waiting for answer from {self.host}:{self.port}"
                        )
                    chunk = await asyncio.wait_for(reader.read(4096), remaining)
                    if not chunk:
                        raise FelicityConnectionError(
                            f"Connection closed by {self.host}:{self.port}"
                        )
                    buffer += chunk
                    payload = _extract_object(buffer)

                try:
                    writer.write(ACK)
                    await writer.drain()
                except OSError:
                    pass
            except TimeoutError as err:
                raise FelicityConnectionError(
                    f"Timeout talking to {self.host}:{self.port}"
                ) from err
            except OSError as err:
                raise FelicityConnectionError(str(err)) from err
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except OSError:
                    pass

        try:
            data = json.loads(payload)
        except ValueError as err:
            raise FelicityProtocolError(
                f"Invalid JSON from stick: {payload[:120]!r}"
            ) from err
        if not isinstance(data, dict):
            raise FelicityProtocolError("Unexpected answer type")
        return data

    async def async_get_realtime(self) -> dict[str, Any]:
        """Fetch the realtime snapshot."""
        data = await self._query(QUERY_REALTIME)
        if "DevSN" not in data or "PV" not in data:
            raise FelicityProtocolError(
                "Realtime answer misses DevSN/PV, device type not supported"
            )
        return data

    async def async_get_info(self) -> dict[str, Any]:
        """Fetch stick info (serial, rssi, clock)."""
        return await self._query(QUERY_DATE)
