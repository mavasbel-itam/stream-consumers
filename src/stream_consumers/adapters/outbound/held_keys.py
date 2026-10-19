"""Credentials the project keeps in `.env` so each can be tested again (tests/live/test_keys_live.py), although no source reads them."""

from __future__ import annotations

from collections.abc import Sequence

from stream_consumers.domain.models import HeldKey
from stream_consumers.ports.outbound import HeldKeyCatalogPort

MASTODON_APPS = "https://docs.joinmastodon.org/client/token/"
WMATA = "https://developer.wmata.com/"
TFL = "https://api-portal.tfl.gov.uk/"

HELD_KEYS: tuple[HeldKey, ...] = (
    HeldKey(
        "mastodon",
        ("MASTODON_CLIENT_ID", "MASTODON_CLIENT_SECRET"),
        "Mastodon, MASTODON_INSTANCE",
        "Client id and secret of the application that issued MASTODON_ACCESS_TOKEN.",
        MASTODON_APPS,
    ),
    HeldKey(
        "mastodon",
        ("MASTODON_WORLD_ACCESS_TOKEN",),
        "Mastodon, mastodon.world",
        "Access token on mastodon.world (live feeds open). To read it, run with MASTODON_INSTANCE=mastodon.world and "
        "this value as MASTODON_ACCESS_TOKEN.",
        "https://mastodon.world/auth/sign_up",
    ),
    HeldKey(
        "mastodon",
        ("MASTODON_WORLD_CLIENT_ID", "MASTODON_WORLD_CLIENT_SECRET"),
        "Mastodon, mastodon.world",
        "Client id and secret of the application that issued MASTODON_WORLD_ACCESS_TOKEN.",
        MASTODON_APPS,
    ),
    HeldKey(
        "mastodon",
        ("MASTODON_SOCIAL_ACCESS_TOKEN",),
        "Mastodon, mastodon.social",
        "Access token on mastodon.social, whose live feeds are disabled (only deletions are streamed).",
        "https://mastodon.social/auth/sign_up",
    ),
    HeldKey(
        "mastodon",
        ("MASTODON_SOCIAL_CLIENT_ID", "MASTODON_SOCIAL_CLIENT_SECRET"),
        "Mastodon, mastodon.social",
        "Client id and secret of the application that issued MASTODON_SOCIAL_ACCESS_TOKEN.",
        MASTODON_APPS,
    ),
    HeldKey(
        "nta",
        ("NTA_API_KEY_SECONDARY",),
        "National Transport Authority (Ireland)",
        "Secondary key of NTA_API_KEY's subscription.",
        "https://developer.nationaltransport.ie/",
    ),
    HeldKey("wmata", ("WMATA_API_KEY_SECONDARY",), "WMATA", "Secondary key of the 'GTFS' product (WMATA_API_KEY is its primary).", WMATA),
    HeldKey("wmata", ("WMATA_BUS_ROUTES_KEY",), "WMATA", "Primary key of the 'Bus Route and Stop Methods' product.", WMATA),
    HeldKey("wmata", ("WMATA_BUS_ROUTES_KEY_SECONDARY",), "WMATA", "Secondary key of the 'Bus Route and Stop Methods' product.", WMATA),
    HeldKey("wmata", ("WMATA_METRO_ALERTS_KEY",), "WMATA", "Primary key of the 'GTFS Metro Alert' product.", WMATA),
    HeldKey("wmata", ("WMATA_METRO_ALERTS_KEY_SECONDARY",), "WMATA", "Secondary key of the 'GTFS Metro Alert' product.", WMATA),
    HeldKey(
        "tfl",
        ("TFL_APP_KEY_SECONDARY",),
        "Transport for London",
        "Secondary key of the 'AirQuality' subscription (TFL_APP_KEY is its primary).",
        TFL,
    ),
    HeldKey("tfl", ("TFL_OCCUPANCY_KEY",), "Transport for London", "Primary key of the 'Occupancy' subscription.", TFL),
    HeldKey("tfl", ("TFL_OCCUPANCY_KEY_SECONDARY",), "Transport for London", "Secondary key of the 'Occupancy' subscription.", TFL),
    HeldKey("tfl", ("TFL_CROWDING_KEY",), "Transport for London", "Primary key of the 'Crowding' subscription.", TFL),
    HeldKey("tfl", ("TFL_CROWDING_KEY_SECONDARY",), "Transport for London", "Secondary key of the 'Crowding' subscription.", TFL),
    HeldKey("tfl", ("TFL_TRACKERNET_KEY",), "Transport for London", "Primary key of the 'Trackernet' subscription.", TFL),
    HeldKey("tfl", ("TFL_TRACKERNET_KEY_SECONDARY",), "Transport for London", "Secondary key of the 'Trackernet' subscription.", TFL),
    HeldKey(
        "coinbase",
        ("COINBASE_CDP_KEY_ID", "COINBASE_CDP_KEY_SECRET"),
        "Coinbase Developer Platform",
        "CDP Secret API Key (Ed25519, view only). The coinbase source reads the public Exchange feed and needs no key.",
        "https://portal.cdp.coinbase.com/",
    ),
    HeldKey(
        "bitso",
        ("BITSO_API_KEY", "BITSO_API_SECRET"),
        "Bitso",
        "Private API key and secret (HMAC-SHA256 signed requests). The bitso source reads the public WebSocket and needs no key.",
        "https://bitso.com/api_setup",
    ),
    HeldKey(
        "binance",
        ("BINANCE_API_KEY", "BINANCE_API_SECRET"),
        "Binance",
        "API key and secret key (HMAC-SHA256 signed requests), reading permission only. The binance source reads the "
        "public streams and needs no key.",
        "https://www.binance.com/en/my/settings/api-management",
    ),
)


class StaticHeldKeyCatalog(HeldKeyCatalogPort):
    def __init__(self, keys: Sequence[HeldKey] = HELD_KEYS) -> None:
        names = [n for k in keys for n in k.env_vars]
        duplicates = sorted({n for n in names if names.count(n) > 1})
        if duplicates:
            raise ValueError(f"held keys name a variable twice: {', '.join(duplicates)}")
        self._keys = tuple(keys)

    def held_keys(self) -> Sequence[HeldKey]:
        return self._keys
