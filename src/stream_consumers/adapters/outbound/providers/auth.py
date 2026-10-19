"""Request authentication adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping

from stream_consumers.domain.errors import TransportError
from stream_consumers.ports.outbound.providers import HttpClientPort, RequestAuthPort
from stream_consumers.ports.outbound.system import ClockPort


class OAuthClientCredentials(RequestAuthPort):
    """OAuth 2 client-credentials grant (RFC 6749 section 4.4): the token is requested on first use
    and again `margin_s` seconds before it expires, or after `invalidate()`."""

    def __init__(
        self, http: HttpClientPort, clock: ClockPort, token_url: str, client_id: str, client_secret: str, margin_s: float = 60.0
    ) -> None:
        self._http = http
        self._clock = clock
        self._token_url = token_url
        self._fields = {"grant_type": "client_credentials", "client_id": client_id, "client_secret": client_secret}
        self._margin_s = margin_s
        self._token: str | None = None
        self._expires_at = 0.0

    async def headers(self) -> Mapping[str, str]:
        if self._token is None or self._clock.monotonic() >= self._expires_at:
            await self._renew()
        return {"Authorization": f"Bearer {self._token}"}

    def invalidate(self) -> None:
        self._token = None

    async def _renew(self) -> None:
        response = await self._http.post_form(self._token_url, self._fields)
        if response.status != 200:
            raise TransportError(f"token request refused: HTTP {response.status}: {response.body[:200]!r}")
        try:
            document = json.loads(response.body)
            token = document["access_token"]
            lifetime = float(document.get("expires_in", 300))
        except (ValueError, KeyError, TypeError) as exc:
            raise TransportError(f"token response without access_token: {response.body[:200]!r}") from exc
        if not isinstance(token, str) or not token:
            raise TransportError("token response with an empty access_token")
        self._token = token
        self._expires_at = self._clock.monotonic() + max(0.0, lifetime - self._margin_s)
