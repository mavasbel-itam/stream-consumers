"""Every key in `.env`, read by a source or held, against its provider (Internet access required; never run in CI).

For each credential: the stored value must be accepted, a damaged copy refused, and a request without it refused
where the provider requires a key (accepted where the key is optional). Values are never printed.

Run: uv run pytest tests/live/test_keys_live.py -m live
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import aiohttp
import pytest
import websockets
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from stream_consumers.adapters.inbound.cli import USER_AGENT
from stream_consumers.adapters.outbound.held_keys import StaticHeldKeyCatalog
from stream_consumers.adapters.outbound.registry import FactoryRegistry
from stream_consumers.adapters.outbound.sources import FACTORIES
from stream_consumers.adapters.outbound.system import EnvSecretProvider
from stream_consumers.application.configuration_service import ConfigurationService
from stream_consumers.domain.models import ConfigKind
from tests.support import deps

pytestmark = pytest.mark.live
ENV = EnvSecretProvider(os.environ, Path(os.environ.get("KEYS_ENV_FILE", ".env")))
TIMEOUT = aiohttp.ClientTimeout(total=60)

Values = Mapping[str, str] | None
"""The credential's values; None means the request is sent without them."""


@dataclass(frozen=True)
class Answer:
    accepted: bool
    evidence: str
    """Status and the start of the body, for the assertion message (never a key)."""


class KeyProbe(ABC):
    """One read-only request that a provider answers differently with a valid key."""

    def __init__(self, env_vars: tuple[str, ...], key_required: bool = True) -> None:
        self.env_vars = env_vars
        self.key_required = key_required

    @abstractmethod
    async def attempt(self, session: aiohttp.ClientSession, values: Values) -> Answer: ...


class HttpProbe(KeyProbe):
    """`request(values)` gives method, URL, headers and form; `accepts(status, body)` judges the answer."""

    def __init__(
        self,
        env_vars: tuple[str, ...],
        request: Callable[[Values], tuple[str, str, Mapping[str, str], Mapping[str, str] | None]],
        accepts: Callable[[int, str], bool] = lambda status, body: status == 200,
        key_required: bool = True,
    ) -> None:
        super().__init__(env_vars, key_required)
        self._request = request
        self._accepts = accepts

    async def attempt(self, session: aiohttp.ClientSession, values: Values) -> Answer:
        method, url, headers, form = self._request(values)
        async with session.request(method, url, headers={"User-Agent": USER_AGENT, **headers}, data=form) as r:
            body = await r.text(errors="replace")
            return Answer(self._accepts(r.status, body), f"HTTP {r.status} {body[:100]!r}")


class AisstreamProbe(KeyProbe):
    """aisstream.io sends ship messages after a valid subscription and silently drops the connection otherwise."""

    async def attempt(self, session: aiohttp.ClientSession, values: Values) -> Answer:
        subscription: dict[str, object] = {"BoundingBoxes": [[[-90, -180], [90, 180]]]}
        if values is not None:
            subscription["APIKey"] = values["AISSTREAM_API_KEY"]
        try:
            async with websockets.connect("wss://stream.aisstream.io/v0/stream", user_agent_header=USER_AGENT) as ws:
                await ws.send(json.dumps(subscription))
                message = await asyncio.wait_for(ws.recv(), 20)
                return Answer(True, f"message {str(message)[:60]!r}")
        except (websockets.ConnectionClosed, TimeoutError) as exc:
            return Answer(False, type(exc).__name__)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def get(url: str, headers: Mapping[str, str] | None = None) -> tuple[str, str, Mapping[str, str], None]:
    return "GET", url, headers or {}, None


def one(values: Values, name: str) -> str:
    return "" if values is None else values[name]


def header_probe(name: str, url: str, header: str, key_required: bool = True) -> HttpProbe:
    return HttpProbe((name,), lambda v: get(url, {} if v is None else {header: v[name]}), key_required=key_required)


def mastodon_token(name: str, instance: Callable[[], str]) -> HttpProbe:
    return HttpProbe(
        (name,), lambda v: get(f"https://{instance()}/api/v1/accounts/verify_credentials", {} if v is None else bearer(v[name]))
    )


def mastodon_app(client_id: str, client_secret: str, instance: Callable[[], str]) -> HttpProbe:
    def request(v: Values) -> tuple[str, str, Mapping[str, str], Mapping[str, str]]:
        form = {"grant_type": "client_credentials", "redirect_uri": "urn:ietf:wg:oauth:2.0:oob", "scope": "read"}
        if v is not None:
            form |= {"client_id": v[client_id], "client_secret": v[client_secret]}
        return "POST", f"https://{instance()}/oauth/token", {}, form

    return HttpProbe((client_id, client_secret), request, lambda status, body: status == 200 and '"access_token"' in body)


def tfl(name: str) -> HttpProbe:
    # TfL also answers without a key; a wrong key gets 429 "Invalid app_key is provided."
    return HttpProbe(
        (name,),
        lambda v: get("https://api.tfl.gov.uk/Line/Mode/tube/Status" + ("" if v is None else f"?app_key={v[name]}")),
        key_required=False,
    )


WMATA_FEED = "https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb"
NTA_FEED = "https://api.nationaltransport.ie/gtfsr/v2/Vehicles"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def coinbase_jwt(key_id: str, secret: str, uri: str) -> str:
    """CDP Secret API Key (Ed25519): base64 of the 32-byte seed and the 32-byte public key; JWT valid 2 minutes."""
    raw = base64.b64decode(secret + "==")
    key = Ed25519PrivateKey.from_private_bytes(raw[:32]) if len(raw) == 64 else Ed25519PrivateKey.generate()
    if key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw) != raw[32:]:
        key = Ed25519PrivateKey.generate()  # a secret whose halves disagree is a broken key: sign with an unregistered one
    now = int(time.time())
    header = {"alg": "EdDSA", "typ": "JWT", "kid": key_id, "nonce": secrets.token_hex(16)}
    claims = {"sub": key_id, "iss": "cdp", "aud": ["cdp_service"], "nbf": now, "exp": now + 120, "uri": uri}
    message = b64url(json.dumps(header).encode()) + "." + b64url(json.dumps(claims).encode())
    return message + "." + b64url(key.sign(message.encode()))


def coinbase(v: Values) -> tuple[str, str, Mapping[str, str], None]:
    path = "api.coinbase.com/api/v3/brokerage/key_permissions"
    if v is None:
        return get(f"https://{path}")
    return get(f"https://{path}", bearer(coinbase_jwt(v["COINBASE_CDP_KEY_ID"], v["COINBASE_CDP_KEY_SECRET"], f"GET {path}")))


def bitso(v: Values) -> tuple[str, str, Mapping[str, str], None]:
    """Signed GET (https://docs.bitso.com/bitso-api/docs/create-signed-requests): HMAC-SHA256 of nonce + method + path."""
    path = "/api/v3/balance/"
    if v is None:
        return get(f"https://api.bitso.com{path}")
    nonce = str(time.time_ns() // 1_000_000)
    signature = hmac.new(v["BITSO_API_SECRET"].encode(), f"{nonce}GET{path}".encode(), hashlib.sha256).hexdigest()
    return get(f"https://api.bitso.com{path}", {"Authorization": f"Bitso {v['BITSO_API_KEY']}:{nonce}:{signature}"})


def bitso_accepts(status: int, body: str) -> bool:
    return status == 200 and json.loads(body)["success"] is True


def binance(v: Values) -> tuple[str, str, Mapping[str, str], None]:
    """Signed GET of the key's own permissions, HMAC-SHA256 of the query string with the secret key (endpoint as in
    Binance's connector: https://github.com/binance/binance-connector-python/blob/master/clients/wallet/src/binance_sdk_wallet/rest_api/api/account_api.py)."""
    path = "https://api.binance.com/sapi/v1/account/apiRestrictions"
    query = f"timestamp={time.time_ns() // 1_000_000}&recvWindow=10000"
    if v is None:
        return get(f"{path}?{query}")
    signature = hmac.new(v["BINANCE_API_SECRET"].encode(), query.encode(), hashlib.sha256).hexdigest()
    return get(f"{path}?{query}&signature={signature}", {"X-MBX-APIKEY": v["BINANCE_API_KEY"]})


def binance_accepts(status: int, body: str) -> bool:
    """Accepted only while the key can read and can neither trade nor withdraw."""
    if status != 200:
        return False
    permissions = json.loads(body)
    return permissions["enableReading"] is True and not any(
        permissions[p]
        for p in ("enableSpotAndMarginTrading", "enableWithdrawals", "enableInternalTransfer", "enableFutures", "enableMargin")
    )


def cta_train_accepts(status: int, body: str) -> bool:
    return status == 200 and json.loads(body)["ctatt"]["errCd"] == "0"


def cta_bus_accepts(status: int, body: str) -> bool:
    return status == 200 and "routes" in json.loads(body)["bustime-response"]


def mastodon_instance() -> str:
    (default,) = (s.default for f in FACTORIES if f.descriptor.id == "mastodon" for s in f.descriptor.settings)
    return ENV.get("MASTODON_INSTANCE") or default


class FinkKafkaProbe(KeyProbe):
    def __init__(self) -> None:
        super().__init__(("FINK_KAFKA_SERVERS", "FINK_GROUP_ID"))

    async def attempt(self, session: aiohttp.ClientSession, values: Values) -> Answer:
        if values is None:
            return Answer(False, "missing Fink credentials")
        try:
            from aiokafka import AIOKafkaConsumer

            consumer = AIOKafkaConsumer(
                group_id=values["FINK_GROUP_ID"],
                bootstrap_servers=values["FINK_KAFKA_SERVERS"],
                request_timeout_ms=5000,
            )
            await consumer.start()
            await consumer.stop()
            return Answer(True, "Fink Kafka connected")
        except Exception as exc:
            return Answer(False, f"Fink Kafka error: {exc}")


PROBES: tuple[KeyProbe, ...] = (
    AisstreamProbe(("AISSTREAM_API_KEY",)),
    HttpProbe(
        ("CTA_BUS_KEY",),
        lambda v: get(f"https://www.ctabustracker.com/bustime/api/v3/getroutes?key={one(v, 'CTA_BUS_KEY')}&format=json"),
        cta_bus_accepts,
    ),
    HttpProbe(
        ("CTA_TRAIN_KEY",),
        lambda v: get(f"https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key={one(v, 'CTA_TRAIN_KEY')}&rt=Red&outputType=JSON"),
        cta_train_accepts,
    ),
    HttpProbe(
        ("ENTSOE_TOKEN",),
        lambda v: get(
            "https://web-api.tp.entsoe.eu/api?documentType=A65&processType=A16&outBiddingZone_Domain=10YFR-RTE------C"
            f"&periodStart=202610010000&periodEnd=202610010100&securityToken={one(v, 'ENTSOE_TOKEN')}"
        ),
    ),
    mastodon_token("MASTODON_ACCESS_TOKEN", mastodon_instance),
    mastodon_app("MASTODON_CLIENT_ID", "MASTODON_CLIENT_SECRET", mastodon_instance),
    mastodon_token("MASTODON_WORLD_ACCESS_TOKEN", lambda: "mastodon.world"),
    mastodon_app("MASTODON_WORLD_CLIENT_ID", "MASTODON_WORLD_CLIENT_SECRET", lambda: "mastodon.world"),
    mastodon_token("MASTODON_SOCIAL_ACCESS_TOKEN", lambda: "mastodon.social"),
    mastodon_app("MASTODON_SOCIAL_CLIENT_ID", "MASTODON_SOCIAL_CLIENT_SECRET", lambda: "mastodon.social"),
    header_probe("MBTA_API_KEY", "https://api-v3.mbta.com/vehicles?page[limit]=1", "x-api-key", key_required=False),
    HttpProbe(
        ("MTA_BUSTIME_KEY",),
        lambda v: get(
            "https://bustime-classic.mta.info/api/siri/vehicle-monitoring.json?LineRef=MTA%20NYCT_M15"
            f"&VehicleMonitoringDetailLevel=minimum&key={one(v, 'MTA_BUSTIME_KEY')}"
        ),
    ),
    header_probe("NTA_API_KEY", NTA_FEED, "x-api-key"),
    header_probe("NTA_API_KEY_SECONDARY", NTA_FEED, "x-api-key"),
    HttpProbe(
        ("OPENSKY_CLIENT_ID", "OPENSKY_CLIENT_SECRET"),
        lambda v: (
            "POST",
            "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token",
            {},
            {"grant_type": "client_credentials"}
            | ({} if v is None else {"client_id": v["OPENSKY_CLIENT_ID"], "client_secret": v["OPENSKY_CLIENT_SECRET"]}),
        ),
    ),
    tfl("TFL_APP_KEY"),
    tfl("TFL_APP_KEY_SECONDARY"),
    tfl("TFL_OCCUPANCY_KEY"),
    tfl("TFL_OCCUPANCY_KEY_SECONDARY"),
    tfl("TFL_CROWDING_KEY"),
    tfl("TFL_CROWDING_KEY_SECONDARY"),
    tfl("TFL_TRACKERNET_KEY"),
    tfl("TFL_TRACKERNET_KEY_SECONDARY"),
    header_probe("WMATA_API_KEY", WMATA_FEED, "api_key"),
    header_probe("WMATA_API_KEY_SECONDARY", WMATA_FEED, "api_key"),
    header_probe("WMATA_BUS_ROUTES_KEY", "https://api.wmata.com/Bus.svc/json/jRoutes", "api_key"),
    header_probe("WMATA_BUS_ROUTES_KEY_SECONDARY", "https://api.wmata.com/Bus.svc/json/jRoutes", "api_key"),
    header_probe("WMATA_METRO_ALERTS_KEY", "https://api.wmata.com/gtfs/rail-gtfsrt-alerts.pb", "api_key"),
    header_probe("WMATA_METRO_ALERTS_KEY_SECONDARY", "https://api.wmata.com/gtfs/rail-gtfsrt-alerts.pb", "api_key"),
    HttpProbe(("COINBASE_CDP_KEY_ID", "COINBASE_CDP_KEY_SECRET"), coinbase),
    HttpProbe(("BITSO_API_KEY", "BITSO_API_SECRET"), bitso, bitso_accepts),
    HttpProbe(("BINANCE_API_KEY", "BINANCE_API_SECRET"), binance, binance_accepts),
    HttpProbe(
        ("LASAIR_API_TOKEN",),
        lambda v: get(
            "https://api.lasair.lsst.ac.uk/api/query/?selected=diaObjectId&tables=objects&conditions=diaObjectId%3E0&limit=1",
            {} if v is None else {"Authorization": f"Token {v['LASAIR_API_TOKEN']}"},
        ),
    ),
    HttpProbe(
        ("GFW_API_TOKEN",),
        lambda v: get(
            "https://gateway.api.globalfishingwatch.org/v3/events?datasets[0]=public-global-fishing-events%3Alatest"
            "&start-date=2026-09-01&end-date=2026-09-02&limit=1&offset=0",
            {} if v is None else bearer(v["GFW_API_TOKEN"]),
        ),
    ),
    FinkKafkaProbe(),
)


def damaged(value: str) -> str:
    """The same value with its last four characters changed within their class (digit, letter, other)."""

    def shift(c: str) -> str:
        if c.isdigit():
            return str((int(c) + 1) % 10)
        if c.isalpha():
            base = "a" if c.islower() else "A"
            return chr((ord(c) - ord(base) + 1) % 26 + ord(base)) if c.isascii() else "x"
        return "x" if c != "x" else "y"

    return value[:-4] + "".join(shift(c) for c in value[-4:])


def keys_in_env() -> Sequence[str]:
    configuration = ConfigurationService(FactoryRegistry(FACTORIES, deps()), ENV, StaticHeldKeyCatalog())
    return [r.env_var for r in configuration.status() if r.kind in (ConfigKind.SECRET, ConfigKind.HELD)]


def test_every_key_has_exactly_one_probe() -> None:
    probed = [n for p in PROBES for n in p.env_vars]
    assert sorted(probed) == sorted(keys_in_env())


async def run(probe: KeyProbe, values: Values) -> Answer:
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        return await probe.attempt(session, values)


@pytest.mark.parametrize("probe", PROBES, ids=lambda p: "+".join(p.env_vars))
async def test_key_is_accepted_and_a_damaged_copy_refused(probe: KeyProbe) -> None:
    stored = {name: ENV.get(name) for name in probe.env_vars}
    if any(v is None for v in stored.values()):
        pytest.skip(f"not set: {', '.join(n for n, v in stored.items() if v is None)}")
    values = {n: str(v) for n, v in stored.items()}
    valid = await run(probe, values)
    assert valid.accepted, f"stored value refused: {valid.evidence}"
    last = probe.env_vars[-1]
    broken = await run(probe, {**values, last: damaged(values[last])})
    assert not broken.accepted, f"damaged value accepted: {broken.evidence}"
    missing = await run(probe, None)
    assert missing.accepted is not probe.key_required, f"without the key: {missing.evidence}"
