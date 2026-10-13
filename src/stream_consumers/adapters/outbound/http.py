"""HTTP client over aiohttp."""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping

import aiohttp

from stream_consumers.domain.errors import TransportError
from stream_consumers.ports.outbound import HttpClientPort, HttpResponse

CHUNK = 1 << 20


class AiohttpClient(HttpClientPort):
    """One shared session, created on first use; `user_agent` is sent on every request."""

    def __init__(self, user_agent: str, timeout_s: float = 120.0, stream_timeout_s: float = 900.0) -> None:
        self._headers = {"User-Agent": user_agent}
        self._timeout = aiohttp.ClientTimeout(total=timeout_s)
        self._stream_timeout = aiohttp.ClientTimeout(total=stream_timeout_s, sock_read=timeout_s)
        self._session: aiohttp.ClientSession | None = None

    def _client(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self._headers)
        return self._session

    async def get(self, url: str, headers: Mapping[str, str] | None = None) -> HttpResponse:
        async with self._client().get(url, headers=dict(headers or {}), timeout=self._timeout) as r:
            return HttpResponse(r.status, await r.read(), dict(r.headers))

    async def post_json(self, url: str, body: object, headers: Mapping[str, str] | None = None) -> HttpResponse:
        async with self._client().post(url, json=body, headers=dict(headers or {}), timeout=self._timeout) as r:
            return HttpResponse(r.status, await r.read(), dict(r.headers))

    async def stream(self, url: str, headers: Mapping[str, str] | None = None) -> AsyncIterator[bytes]:
        async with self._client().get(url, headers=dict(headers or {}), timeout=self._stream_timeout) as r:
            if r.status != 200:
                raise TransportError(f"HTTP {r.status} for {url}: {(await r.read())[:200]!r}")
            async for chunk in r.content.iter_any():
                yield chunk

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()
