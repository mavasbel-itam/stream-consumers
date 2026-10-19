"""The source catalog: descriptors, factories and decoders, checked against real captured messages."""

from __future__ import annotations

import importlib
import json
import struct
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

import pytest

from stream_consumers.adapters.outbound.auth import OAuthClientCredentials
from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources import FACTORIES
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.sources.mbta_v3 import MbtaStreamDecoder
from stream_consumers.adapters.outbound.sources.wmata import FeedTaggedGtfsRealtimeDecoder
from stream_consumers.adapters.outbound.transports.base import DecodingEventSource, MergedEventSource
from stream_consumers.adapters.outbound.transports.http_poll import HttpPollSource
from stream_consumers.adapters.outbound.transports.sse import SseSource
from stream_consumers.domain.errors import DecodeError, MissingCredentialError, TransportError
from stream_consumers.domain.models import Credential, Group, RawMessage
from stream_consumers.domain.policy import PersonalDataMasker
from stream_consumers.ports.outbound import Credentials, DecoderPort, EventSourcePort, SourceDependencies
from tests.support import ScriptedSource, deps, descriptor, messages

BY_ID = {f.descriptor.id: f for f in FACTORIES}
ROOT = Path(__file__).resolve().parents[2]


def module(source_id: str):  # type: ignore[no-untyped-def]
    return importlib.import_module(f"stream_consumers.adapters.outbound.sources.{source_id}")


def all_credentials(source_id: str) -> dict[str, str]:
    credential = BY_ID[source_id].descriptor.credential
    return {name: f"test-{name.lower()}" for name in (credential.env_vars if credential else ())}


def decoder_of(source_id: str) -> DecoderPort:
    """The decoder of the source as built with only the credentials it requires (keyless path when optional)."""
    credential = BY_ID[source_id].descriptor.credential
    source = BY_ID[source_id].create(deps(secrets=all_credentials(source_id) if credential and credential.required else {}))
    if isinstance(source, MergedEventSource):
        source = source._children[0]
    assert isinstance(source, DecodingEventSource)
    return source._decoder


class TestCatalog:
    def test_66_sources_in_four_groups(self) -> None:
        groups = [f.descriptor.group for f in FACTORIES]
        assert len(FACTORIES) == 66 == len(BY_ID)
        counts = tuple(groups.count(g) for g in (Group.KEYLESS, Group.PROJECT_DOCUMENT, Group.FREE_KEY, Group.CANDIDATE))
        assert counts == (49, 7, 9, 1)

    def test_required_keys_belong_to_measured_free_key_sources_or_candidates(self) -> None:
        required = {f.descriptor.id for f in FACTORIES if f.descriptor.credential and f.descriptor.credential.required}
        assert required == {"aisstream", "cta_bus", "cta_train", "entsoe", "mastodon", "mta_bustime", "nta", "wmata"}
        assert {f.descriptor.id for f in FACTORIES if f.descriptor.group is Group.CANDIDATE} == {"entsoe"}
        assert {f.descriptor.id for f in FACTORIES if f.descriptor.group is Group.FREE_KEY} == {
            "cta_bus",
            "cta_train",
            "firms",
            "mastodon",
            "mbta_v3",
            "mta_bustime",
            "nta",
            "tfl",
            "wmata",
        }
        assert all(f.descriptor.credential.how_to_get for f in FACTORIES if f.descriptor.credential)  # type: ignore[union-attr]

    def test_project_document_sources(self) -> None:
        assert {f.descriptor.id for f in FACTORIES if f.descriptor.group is Group.PROJECT_DOCUMENT} == {
            "bluesky",
            "wikimedia",
            "gdelt",
            "binance",
            "mempool",
            "opensky",
            "aisstream",
        }

    @pytest.mark.parametrize("source_id", sorted(BY_ID))
    def test_descriptor_matches_its_module(self, source_id: str) -> None:
        d = BY_ID[source_id].descriptor
        assert module(source_id).FACTORY is BY_ID[source_id]
        assert d.docs_url.startswith("https://") and d.terms_url.startswith("https://")
        assert d.name and d.category and d.provider and d.endpoint
        assert all(isinstance(p, str) and p for p in d.personal_fields)

    @pytest.mark.parametrize("source_id", sorted(BY_ID))
    def test_factory_builds_a_source_without_keys_unless_one_is_required(self, source_id: str) -> None:
        credential = BY_ID[source_id].descriptor.credential
        if credential is not None and credential.required:
            with pytest.raises(MissingCredentialError) as error:
                BY_ID[source_id].create(deps())
            assert error.value.env_vars == credential.env_vars
            return
        source = BY_ID[source_id].create(deps())
        assert isinstance(source, EventSourcePort)
        assert source.descriptor is BY_ID[source_id].descriptor

    @pytest.mark.parametrize("source_id", sorted(BY_ID))
    def test_factory_builds_a_source_with_every_credential_set(self, source_id: str) -> None:
        source = BY_ID[source_id].create(deps(secrets=all_credentials(source_id)))
        assert isinstance(source, EventSourcePort) and source.descriptor is BY_ID[source_id].descriptor


class _Keyed(BaseSourceFactory):
    DESCRIPTOR = descriptor("keyed", credential=Credential(("K",), "https://sign.up"))

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"key": credentials}], deps.clock)  # type: ignore[arg-type]


class TestCredentials:
    def test_required_key_missing_raises(self) -> None:
        with pytest.raises(MissingCredentialError) as error:
            _Keyed().create(deps())
        assert error.value.env_vars == ("K",)

    def test_required_key_present_is_passed(self) -> None:
        assert _Keyed().create(deps(secrets={"K": "abc"}))._payloads == [{"key": {"K": "abc"}}]  # type: ignore[attr-defined]

    def test_mbta_key_switches_from_polling_to_streaming(self) -> None:
        keyless = BY_ID["mbta_v3"].create(deps())
        keyed = BY_ID["mbta_v3"].create(deps(secrets={"MBTA_API_KEY": "k"}))
        assert isinstance(keyless, HttpPollSource) and (keyless._interval_s, keyless._headers) == (20.0, {})
        assert isinstance(keyed, SseSource)
        assert keyed._headers == {"Accept": "text/event-stream", "x-api-key": "k"}
        assert keyed._event_types == frozenset({"reset", "add", "update", "remove"})

    def test_keys_are_placed_where_each_provider_documents_them(self) -> None:
        def poll(source_id: str, **secrets: str) -> HttpPollSource:
            source = BY_ID[source_id].create(deps(secrets=secrets))
            assert isinstance(source, HttpPollSource)
            return source

        assert poll("mta_bustime", MTA_BUSTIME_KEY="k")._urls == ("https://gtfsrt.prod.obanyc.com/vehiclePositions?key=k",)
        nta = poll("nta", NTA_API_KEY="k")
        assert (nta._urls, nta._headers, nta._interval_s) == (
            ("https://api.nationaltransport.ie/gtfsr/v2/Vehicles",),
            {"x-api-key": "k"},
            60.0,
        )
        wmata = BY_ID["wmata"].create(deps(secrets={"WMATA_API_KEY": "k"}))
        assert isinstance(wmata, MergedEventSource)
        assert [(c._urls, c._headers) for c in wmata._children] == [  # type: ignore[attr-defined]
            (("https://api.wmata.com/gtfs/bus-gtfsrt-vehiclepositions.pb",), {"api_key": "k"}),
            (("https://api.wmata.com/gtfs/rail-gtfsrt-vehiclepositions.pb",), {"api_key": "k"}),
        ]
        train = poll("cta_train", CTA_TRAIN_KEY="k")
        assert train._urls[0] == "https://lapi.transitchicago.com/api/1.0/ttpositions.aspx?key=k&rt=Red&outputType=JSON"
        assert len(train._urls) == 8 and train._interval_s == 30.0
        assert poll("cta_bus", CTA_BUS_KEY="k")._urls == ("https://www.ctabustracker.com/bustime/api/v3/getroutes?key=k&format=json",)

    def test_opensky_uses_oauth_only_when_both_values_are_set(self) -> None:
        assert BY_ID["opensky"].create(deps())._auth is None  # type: ignore[attr-defined]
        assert BY_ID["opensky"].create(deps(secrets={"OPENSKY_CLIENT_ID": "i"}))._auth is None  # type: ignore[attr-defined]
        keyed = BY_ID["opensky"].create(
            deps(secrets={"OPENSKY_CLIENT_ID": "i", "OPENSKY_CLIENT_SECRET": "s", "OPENSKY_POLL_SECONDS": "90"})
        )
        assert isinstance(keyed._auth, OAuthClientCredentials) and keyed._interval_s == 90.0  # type: ignore[attr-defined]

    def test_aisstream_subscription_carries_key_and_boxes(self) -> None:
        source = BY_ID["aisstream"].create(deps(secrets={"AISSTREAM_API_KEY": "k"}))
        assert source._subscriptions == ({"APIKey": "k", "BoundingBoxes": [[[-90, -180], [90, 180]]]},)  # type: ignore[attr-defined]
        for bad in ("[]", "[[1, 2]]", "[[[1, 2], [3]]]", "{}", "[[[1, 2], [3, 4], [5, 6]]]"):
            with pytest.raises(ValueError, match="AISSTREAM_BOUNDING_BOXES"):
                BY_ID["aisstream"].create(deps(secrets={"AISSTREAM_API_KEY": "k", "AISSTREAM_BOUNDING_BOXES": bad}))

    def test_entsoe_areas_must_not_be_empty(self) -> None:
        with pytest.raises(ValueError, match="EIC"):
            BY_ID["entsoe"].create(deps(secrets={"ENTSOE_TOKEN": "t", "ENTSOE_AREAS": " , "}))

    def test_tfl_key_goes_in_the_query(self) -> None:
        assert BY_ID["tfl"].create(deps())._urls == ("https://api.tfl.gov.uk/Mode/tube/Arrivals",)  # type: ignore[attr-defined]
        assert BY_ID["tfl"].create(deps(secrets={"TFL_APP_KEY": "k"}))._urls == (  # type: ignore[attr-defined]
            "https://api.tfl.gov.uk/Mode/tube/Arrivals?app_key=k",
        )


# Events per captured message. A 0 is a captured control frame (subscription answer, heartbeat) that
# must not count as an event. Sources read from files or several endpoints are tested in the component tier.
EXPECTED = {
    "adsb_fi": [3],
    "aisstream": [0, 1, 1, 1, 1],
    "cta_bus": [0, 3],
    "cta_train": [3],
    "entsoe": [1824],
    "mastodon": [1, 1],
    "adsb_lol": [3],
    "albion": [1, 1, 1],
    "atlas": [0, 1, 1, 1, 1],
    "base_logs": [0, 1, 1, 1, 1],
    "bicing": [3],
    "binance": [1, 1, 1, 1],
    "bitfinex": None,
    "bitso": [0, 1, 1, 1, 1],
    "blockchain": [0, 1, 1, 1, 1],
    "citibike": [3],
    "coinpaprika": [3],
    "ogn": [0, 1, 1, 1, 1],
    "sharpe": [3],
    "ukflood": [3],
    "bluesky": [1, 1, 1, 1],
    "bsc_logs": [0, 1, 1, 1, 1],
    "bybit": [0, 1, 1, 1, 1],
    "coinbase": [0, 1, 1, 1, 1],
    "crossref": [3],
    "deribit": [0, 1, 1, 1, 1],
    "dt_marine": [1, 1, 1, 1],
    "dt_rail": [1, 1, 1, 1],
    "dt_road": [0, 0, 1, 1],
    "ecobici": [3],
    "entur": [3],
    "eth_logs": [0, 1, 1, 1, 1],
    "firms": [3, 3, 3, 3],
    "gemini": [5, 1, 1, 1],
    "hsl": [1, 1, 1, 1],
    "hyperliquid": [0, 30, 30, 30, 1],
    "kraken": [0, 2, 1, 2, 1],
    "mbta_gtfsrt": [3],
    "mbta_v3": [3],
    "mempool": [0, 5, 5, 5, 5],
    "metar": [3],
    "mta_bustime": [3],
    "mta_gtfsrt": [3],
    "ndov": [67, 66, 54, 119],
    "nta": [3],
    "okx": [0, 1, 1, 1, 1],
    "opensky": [3],
    "polygon_logs": [0, 1, 1, 1, 1],
    "polymarket": [0, 2, 2, 2, 2],
    "pskreporter": [1, 1, 1, 1],
    "rbn": [0, 1, 1, 1, 1],
    "ris": [1, 1, 1, 1],
    "seedlink": [1, 1, 1, 1],
    "sensorcomm": [3],
    "solana": [0, 1, 1, 1, 1],
    "tfl": [3],
    "twitch": [0, 1, 1, 1, 1],
    "usgs_water": [3],
    "velib": [3],
    "wikimedia": [1, 1, 1, 1],
    "xrpl": [0, 1, 1, 1, 1],
}


@pytest.mark.parametrize("source_id", sorted(EXPECTED))
def test_captured_messages_decode_to_masked_events(source_id: str) -> None:
    decoder = decoder_of(source_id)
    counts, events = [], []
    for message in messages(source_id):
        decoded = decoder.decode(message)
        counts.append(len(decoded))
        events.extend(decoded)
    if EXPECTED[source_id] is not None:
        assert counts == EXPECTED[source_id]
    assert events and all(isinstance(e, Mapping) and e for e in events)
    masker = PersonalDataMasker(BY_ID[source_id].descriptor.personal_fields)
    assert [masker.leaks(e) for e in events if masker.leaks(e)] == []


def test_bitfinex_maps_channel_ids_from_the_subscription_answers() -> None:
    decoder = decoder_of("bitfinex")
    events = [e for m in messages("bitfinex") for e in decoder.decode(m)]
    assert len(events) == 4 and {e["channel"] for e in events} <= {"trades", "ticker"}
    assert all(e["symbol"].startswith("t") for e in events)


UNRELATED = ['{"unrelated": 1}', "[]", "5", '"text"', "[1, 2]"]
ENVELOPE_DECODERS = [
    "aisstream",
    "cta_bus",
    "cta_train",
    "atlas",
    "base_logs",
    "binance",
    "bitso",
    "blockchain",
    "bluesky",
    "bybit",
    "coinbase",
    "crossref",
    "deribit",
    "entur",
    "gemini",
    "hsl",
    "hyperliquid",
    "kraken",
    "mbta_v3",
    "mempool",
    "okx",
    "opensky",
    "polymarket",
    "ris",
    "solana",
    "sensorcomm",
    "usgs_water",
    "xrpl",
    "bicing",
    "velib",
    "citibike",
    "adsb_fi",
    "bitfinex",
    "ogn",
    "ukflood",
]


@pytest.mark.parametrize("source_id", ENVELOPE_DECODERS)
@pytest.mark.parametrize("body", UNRELATED)
def test_envelope_decoders_ignore_unrelated_frames(source_id: str, body: str) -> None:
    """Negative control: a frame that is not the provider's event envelope yields no event."""
    assert decoder_of(source_id).decode(RawMessage(body)) == []


def decode(source_id: str, body: object, **attributes: str) -> list[Mapping[str, object]]:
    text = body if isinstance(body, str) else json.dumps(body)
    return list(decoder_of(source_id).decode(RawMessage(text, attributes)))


class TestDecoderBranches:
    def test_bitfinex_heartbeats_unknown_channels_and_trade_updates_are_skipped(self) -> None:
        d = decoder_of("bitfinex")
        d.decode(RawMessage(json.dumps({"event": "subscribed", "chanId": 7, "channel": "trades", "symbol": "tBTCUSD"})))
        d.decode(RawMessage(json.dumps({"event": "subscribed", "chanId": 8, "channel": "ticker", "symbol": "tETHUSD"})))
        assert d.decode(RawMessage('[7, "hb"]')) == []
        assert d.decode(RawMessage("[99, [1, 2, 3, 4]]")) == []
        assert d.decode(RawMessage('[7, "tu", [1, 2, 3, 4]]')) == []
        assert d.decode(RawMessage("[7, [[1, 2, 3, 4]]]")) == []
        assert d.decode(RawMessage('[7, "te"]')) == []
        assert d.decode(RawMessage('[8, "hb"]')) == []
        assert d.decode(RawMessage('[7, "te", [1, 2, 3.5, 4]]')) == [
            {"ID": 1, "MTS": 2, "AMOUNT": 3.5, "PRICE": 4, "symbol": "tBTCUSD", "channel": "trades"}
        ]
        assert d.decode(RawMessage(json.dumps({"event": "info", "version": 2}))) == []

    def test_polymarket_frames(self) -> None:
        assert decode("polymarket", "PONG") == []
        single = {"event_type": "last_trade_price", "price": "0.5"}
        assert decode("polymarket", single) == [single]
        assert decode(
            "polymarket",
            [
                1,
                {"event_type": "book"},
                {"event_type": "price_change", "market": "m", "timestamp": "1", "price_changes": [2, {"price": "0.4"}]},
            ],
        ) == [{"market": "m", "timestamp": "1", "event_type": "price_change", "price": "0.4"}]

    def test_okx_pong_is_not_an_event(self) -> None:
        assert decode("okx", "pong") == []

    def test_hsl_needs_exactly_one_wrapping_key(self) -> None:
        assert decode("hsl", {"VP": {"veh": 1}}) == [{"veh": 1, "event_type": "VP"}]
        assert decode("hsl", {"VP": 1}) == []
        assert decode("hsl", {"VP": {}, "DOO": {}}) == []

    def test_twitch_only_privmsg_lines_with_tags(self) -> None:
        assert decode("twitch", ":tmi.twitch.tv 001 justinfan :Welcome") == []
        assert decode("twitch", "@a=1;b=2;x :u!u@u.tmi.twitch.tv PRIVMSG #chan :hola: mundo") == [
            {"a": "1", "b": "2", "channel": "#chan", "message": "hola: mundo"}
        ]

    def test_rbn_ignores_non_spot_lines(self) -> None:
        assert decode("rbn", "Please enter your call:") == []

    def test_seedlink_ignores_info_and_short_packets(self) -> None:
        d = decoder_of("seedlink")
        assert d.decode(RawMessage(b"SLINFO" + b"\x00" * 514)) == []
        assert d.decode(RawMessage(b"SL000001" + b"\x00" * 10)) == []
        assert d.decode(RawMessage(b"XX" + b"\x00" * 518)) == []

    def test_seedlink_header_fields(self) -> None:
        header = b"000001D " + b"ANMO " + b"00" + b"BHZ" + b"IU" + struct.pack(">HHBBBBHHhh", 2026, 286, 7, 8, 9, 0, 1234, 400, 40, 1)
        (event,) = decoder_of("seedlink").decode(RawMessage(b"SL00002A" + header + b"\x00" * (512 - len(header))))
        assert event == {
            "sequence": "00002A",
            "station": "ANMO",
            "location": "00",
            "channel": "BHZ",
            "network": "IU",
            "year": 2026,
            "day_of_year": 286,
            "hour": 7,
            "minute": 8,
            "second": 9,
            "fraction_0001s": 1234,
            "samples": 400,
            "rate_factor": 40,
            "rate_multiplier": 1,
        }

    def test_ndov_keeps_the_envelope(self) -> None:
        events = list(decoder_of("ndov").decode(messages("ndov")[0]))
        assert events[0]["envelope"] and events[0]["messagetype"]

    def test_xrpl_without_meta(self) -> None:
        assert decode("xrpl", {"type": "transaction", "transaction": {"Fee": "10"}}) == [
            {"Fee": "10", "ledger_index": None, "validated": None, "close_time_iso": None, "TransactionResult": None}
        ]

    def test_digitraffic_status_topics_and_topic_fields(self) -> None:
        assert decode("dt_road", {"updated": 1}, topic="tms-v2/status") == []
        assert decode("dt_road", {"value": 3}, topic="tms-v2/23001/5016") == [
            {"feed": "tms-v2", "stationId": "23001", "sensorId": "5016", "value": 3}
        ]
        assert decode("dt_road", {"value": 3}, topic="tms-v2") == [{"feed": "tms-v2", "value": 3}]
        assert decode("dt_marine", [1], topic="vessels-v2/1/location") == []

    def test_gbfs_and_adsb_shapes(self) -> None:
        assert decode("bicing", {"data": {"stations": [{"station_id": "1"}, 2]}, "last_updated": 5}) == [
            {"station_id": "1", "feed_last_updated": 5}
        ]
        velib = {"data": {"stations": [{"station_id": 2}]}, "lastUpdatedOther": 7, "last_updated": 9}
        assert decode("velib", velib) == [{"station_id": 2, "feed_last_updated": 7}]
        assert decode("adsb_lol", {"aircraft": [{"hex": "a"}, 1], "now": 9}) == [{"hex": "a", "feed_now": 9}]

    def test_albion_message_shapes(self) -> None:
        assert decode("albion", {"Orders": [{"Id": 1}]}) == [{"Id": 1}]
        assert decode("albion", [{"Id": 2}]) == [{"Id": 2}]
        assert decode("albion", {"Id": 3}) == [{"Id": 3}]

    def test_sensorcomm_without_values(self) -> None:
        assert decode("sensorcomm", [{"id": 1, "sensordatavalues": None}, 2]) == [{"id": 1}]

    def test_usgs_series_without_values(self) -> None:
        assert (
            decode("usgs_water", {"value": {"timeSeries": [{"sourceInfo": {"s": 1}, "variable": {"v": 1}, "values": [{"value": []}]}]}})
            == []
        )
        assert decode("usgs_water", {"value": 1}) == []

    def test_metar_without_header_is_empty(self) -> None:
        import gzip as gz

        assert decoder_of("metar").decode(RawMessage(gz.compress(b"no header here\n"))) == []

    def test_kraken_snapshots_are_not_updates(self) -> None:
        assert decode("kraken", {"channel": "trade", "type": "snapshot", "data": [{"p": 1}]}) == []
        assert decode("kraken", {"channel": "trade", "type": "update", "data": [{"p": 1}, 2]}) == [{"p": 1, "channel": "trade"}]

    def test_mempool_without_added(self) -> None:
        assert decode("mempool", {"mempool-transactions": {"removed": ["x"]}}) == []

    def test_blockchain_operations_other_than_utx_are_not_events(self) -> None:
        assert decode("blockchain", {"op": "pong"}) == []
        assert decode("blockchain", {"op": "utx", "x": "not a transaction"}) == []
        assert decode("blockchain", {"op": "utx", "x": {"hash": "h"}}) == [{"hash": "h"}]

    def test_ukflood_answer_without_items(self) -> None:
        assert decode("ukflood", {"items": "x"}) == []
        assert decode("ukflood", {"items": [{"@id": "r"}, 3]}) == [{"@id": "r"}]

    # Beacons below are real lines from aprs.glidernet.org:14580 (2026-10-19 00:52 UTC)
    OGN_FLARM = (
        "FNT043EA0>OGNFNT,qAS,AVX1300:/005251h5000.00N/02000.00E'000/000/A=000820 !W00! id07043EA0 +000fpm +0.0rot "
        "FNT14 sF1 cr4 4.9dB +3.6kHz 1e"
    )
    OGN_ADSL = "PAWE5A900>OGADSL,qAS,AVX1126:/005251h5333.01N/01009.52Ez071/000/A=000000 !W67! id03E5A900 +059fpm 51.5dB +4.2kHz gps63x63"
    OGN_SHORT = "ICA342345>OGADSB,qAS,Paracuell:/005253h4030.10N/00334.83W^000/000 !W39! id01342345 C0:TXLU01"

    def test_ogn_flarm_beacon_fields(self) -> None:
        (event,) = decode("ogn", self.OGN_FLARM)
        assert event == {
            "callsign": "FNT043EA0",
            "dstcall": "OGNFNT",
            "receiver": "AVX1300",
            "relay": "qAS",
            "timestamp_hhmmss": "005251",
            "latitude": 50.0,
            "longitude": 20.0,
            "symbol": "/'",
            "address": "043EA0",
            "address_type": 3,
            "aircraft_type": 1,
            "course_deg": 0,
            "ground_speed_kt": 0,
            "altitude_ft": 820,
            "climb_rate_fpm": 0,
            "turn_rate_rot": 0.0,
            "signal_quality_db": 4.9,
            "frequency_offset_khz": 3.6,
            "error_count": 1,
            "other": "FNT14 sF1 cr4",
        }

    def test_ogn_precision_hemispheres_and_optional_parts(self) -> None:
        (adsl,) = decode("ogn", self.OGN_ADSL)
        assert adsl["latitude"] == round(53 + 33.016 / 60, 6) and adsl["longitude"] == round(10 + 9.527 / 60, 6)
        assert adsl["gps_quality"] == "63x63" and "other" not in adsl
        (short,) = decode("ogn", self.OGN_SHORT)
        assert short["longitude"] == -round(3 + 34.839 / 60, 6) and short["flight_id"] == "TXLU01"
        assert "altitude_ft" not in short
        (still,) = decode("ogn", "X>OGFLR,qAS,R:/005251h4000.00S/00100.00W'id0A123456 h0F s7.07 rABCDEF Sq1200 FL010.5 -1.2rot 2e")
        assert (still["latitude"], still["longitude"]) == (-40.0, -1.0) and "course_deg" not in still
        assert (still["hardware_version"], still["software_version"], still["real_address"]) == ("0F", "7.07", "ABCDEF")

    @pytest.mark.parametrize(
        "line",
        [
            "# aprsc 2.1.20-gf.5-g0178a1b 19 Oct 2026 00:53:13 GMT GLIDERN3 85.188.1.173:14580",
            "GrundNW>OGNFNT,TCPIP*,qAC,GLIDERN2:/005252h5058.22NI00807.91E&/A=001315",
            "AVX1300>OGNSDR,TCPIP*,qAC,GLIDERN3:>005250h v0.3.2 CPU:0.4",
            "FLRDDA5BA>OGFLR,qAS,LFMX:/160828h4415.41N/00600.03E'342/049/A=005524 id8ADDA5BA -454fpm",
            "FLRDDA5BA>OGFLR,qAS,LFMX:/160828h4415.41N/00600.03E'342/049/A=005524 id4ADDA5BA -454fpm",
        ],
        ids=["server-comment", "receiver-beacon", "status", "stealth", "no-tracking"],
    )
    def test_ogn_lines_that_are_not_published_aircraft_beacons(self, line: str) -> None:
        assert decode("ogn", line) == []

    def test_gemini_update_without_events(self) -> None:
        assert decode("gemini", {"type": "update"}) == []

    def test_plain_json_sources_keep_every_mapping(self) -> None:
        for source_id in ("pskreporter", "wikimedia", "tfl", "coinpaprika", "sharpe"):
            assert isinstance(decoder_of(source_id), JsonDecoder)
            assert decode(source_id, [{"a": 1}]) == [{"a": 1}]


# ---------------------------------------------------------------- key-gated sources (documentation examples until a key exists)
def doc_fixture(source_id: str) -> dict[str, object]:
    return json.loads((ROOT / "tests" / "fixtures" / "raw" / f"{source_id}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("source_id", ["entsoe"])
def test_documentation_fixtures_say_where_they_come_from(source_id: str) -> None:
    fixture = doc_fixture(source_id)
    assert str(fixture["origin"]).startswith("official documentation example")
    assert str(fixture["documentation_url"]).startswith("https://") and isinstance(fixture["corrections"], list)


@pytest.mark.parametrize("source_id", ["aisstream", "cta_bus", "cta_train", "mastodon", "mbta_v3_stream", "mta_bustime", "nta", "wmata"])
def test_fixtures_captured_with_a_key_say_when_and_that_the_key_is_not_stored(source_id: str) -> None:
    fixture = doc_fixture(source_id)
    assert datetime.fromisoformat(str(fixture["captured_at"])).tzinfo is not None
    assert "origin" not in fixture and "is not stored" in str(fixture["note"])


def test_only_sources_that_need_a_longer_window_declare_one() -> None:
    # tfl: 60-s shared cache; nta: one call per 60 s; firms, sensorcomm: whole files before the first event;
    # coinpaprika, sharpe: snapshots refreshed about every 5 min (up to 10); ukflood: two polls 15 min apart;
    # citibike: regenerated every 60 s
    assert {f.descriptor.id: f.descriptor.min_window_s for f in FACTORIES if f.descriptor.min_window_s} == {
        "citibike": 150.0,
        "coinpaprika": 630.0,
        "firms": 600.0,
        "nta": 150.0,
        "sensorcomm": 600.0,
        "sharpe": 630.0,
        "tfl": 150.0,
        "ukflood": 960.0,
    }


class TestKeyGatedDecoders:
    def test_mbta_stream_events_keep_their_type_and_the_opening_reset_is_not_an_event(self) -> None:
        decoder = MbtaStreamDecoder()
        decoded = [decoder.decode(m) for m in messages("mbta_v3_stream")]  # captured 2026-10-18 with a key
        assert [len(d) for d in decoded] == [0, 1, 1, 1]
        assert [d[0]["event_type"] for d in decoded[1:]] == ["add", "update", "remove"]
        assert [d[0]["id"] for d in decoded[1:]] == ["y3131", "y1323", "y1843"]
        assert decoded[3][0] == {"id": "y1843", "type": "vehicle", "event_type": "remove"}
        reset = messages("mbta_v3_stream")[0]
        assert len(json.loads(reset.body)) == 2 and reset.attributes == {"event": "reset"}  # the snapshot holds two vehicles
        assert decoder.decode(RawMessage(reset.body, {"event": "add"})) != []  # same body under another event type counts

    def test_aisstream_puts_type_and_metadata_on_the_body(self) -> None:
        events = [e for m in messages("aisstream") for e in decoder_of("aisstream").decode(m)]  # captured 2026-10-18
        assert [e["MessageType"] for e in events] == [
            "PositionReport",
            "StandardClassBPositionReport",
            "ShipStaticData",
            "StaticDataReport",
        ]
        event = events[0]
        assert event["UserID"] == event["MetaData"]["MMSI"] == 211437340 and event["Sog"] == 9.4
        assert event["MetaData"]["ShipName"] == "TOLLERORT" and event["MetaData"]["latitude"] == 53.54225
        assert decode("aisstream", {"MessageType": "PositionReport", "Message": {"PositionReport": {"Sog": 1}}}) == [
            {"Sog": 1, "MessageType": "PositionReport", "MetaData": {}}
        ]
        assert decode("aisstream", {"MessageType": "PositionReport", "Message": {"Other": {}}}) == []

    def test_mastodon_events(self) -> None:
        update, delete = [e for m in messages("mastodon") for e in decoder_of("mastodon").decode(m)]
        assert update["event_type"] == "update" and update["id"] == "117462650988898961"  # captured 2026-10-18, masked
        assert delete == {"event_type": "delete", "id": "116945619957947049"}
        assert update["account.username"] == update["content"] == "<masked>"
        assert decode("mastodon", {"id": "1"}, event="status.update") == [{"id": "1", "event_type": "status.update"}]
        assert decode("mastodon", "[1]", event="update") == []
        assert decode("mastodon", {"x": 1}, event="notification") == []
        with pytest.raises(DecodeError):
            decode("mastodon", "{not json", event="update")

    def test_cta_train_errors_and_single_objects(self) -> None:
        trains = [e for m in messages("cta_train") for e in decoder_of("cta_train").decode(m)]  # captured 2026-10-18 with a key
        assert [(t["route"], t["rn"]) for t in trains] == [("red", "818"), ("red", "821"), ("red", "827")]
        assert {t["tmst"] for t in trains} == {"2026-10-17T22:25:41"} and len(trains[0]) == 17
        one = {"ctatt": {"errCd": "0", "route": {"@name": "g", "train": {"rn": "1"}}}}
        assert decode("cta_train", one) == [{"rn": "1", "route": "g", "tmst": None}]
        assert decode("cta_train", {"ctatt": {"errCd": "0"}}) == []
        assert decode("cta_train", {"ctatt": {"errCd": "0", "route": [1, {"@name": "p", "train": [2]}]}}) == []
        with pytest.raises(TransportError, match="error 101: Invalid API key"):
            decode("cta_train", {"ctatt": {"errCd": "101", "errNm": "Invalid API key"}})

    def test_mta_bustime_vehicles_captured_with_a_key(self) -> None:
        events = [e for m in messages("mta_bustime") for e in decoder_of("mta_bustime").decode(m)]  # captured 2026-10-18
        assert [e["id"] for e in events] == ["MTA NYCT_9773", "MTA NYCT_7114", "MTA NYCT_8438"]
        assert all(e["vehicle"]["vehicle"]["id"] == e["id"] for e in events)

    def test_wmata_bus_and_rail_feeds_captured_with_a_key(self) -> None:
        bus, rail = messages("wmata")  # captured 2026-10-18 with a key
        events = FeedTaggedGtfsRealtimeDecoder("bus").decode(bus) + FeedTaggedGtfsRealtimeDecoder("rail").decode(rail)
        assert [(e["feed"], e["id"]) for e in events] == [
            ("bus", "4728"),
            ("bus", "4722"),
            ("bus", "4726"),
            ("rail", "0"),
            ("rail", "1"),
            ("rail", "2"),
        ]
        assert [e["vehicle"]["vehicle"]["id"] for e in events[3:]] == ["006", "016", "021"]

    def test_nta_vehicles_captured_with_a_key(self) -> None:
        events = [e for m in messages("nta") for e in decoder_of("nta").decode(m)]  # captured 2026-10-18 with a key
        assert [(e["id"], e["vehicle"]["vehicle"]["id"]) for e in events] == [("V1", "214"), ("V2", "250"), ("V3", "328")]
        assert {e["feedTimestamp"] for e in events} == {1792297823} and events[0]["vehicle"]["trip"]["routeId"] == "1 41 c a"
        assert all(set(e["vehicle"]["position"]) == {"latitude", "longitude"} for e in events)

    def test_cta_bus_ignores_no_data_but_not_other_errors(self) -> None:
        events = [e for m in messages("cta_bus") for e in decoder_of("cta_bus").decode(m)]
        assert [e["vid"] for e in events] == ["8678", "7963", "8683"]  # captured 2026-10-17 with a key
        no_data = {"bustime-response": {"error": [{"rt": "X9", "msg": "No data found for parameter"}], "vehicle": {"vid": "7"}}}
        assert decode("cta_bus", no_data) == [{"vid": "7"}]
        with pytest.raises(TransportError, match="No API access key supplied"):
            decode("cta_bus", {"bustime-response": {"error": [{"msg": "No API access key supplied"}]}})

    def test_entsoe_points_and_times(self) -> None:
        events = [e for m in messages("entsoe") for e in decoder_of("entsoe").decode(m)]
        first, second = events[0], events[1]
        assert first["area"] == "10Y1001A1001A83F" and first["direction"] == "generation" and first["psr_type"] == "B01"
        assert (first["position"], first["timestamp"], second["timestamp"]) == (1, "2023-08-15T22:00Z", "2023-08-15T22:15Z")
        assert isinstance(first["quantity"], float) and first["unit"] == "MAW" and first["resolution"] == "PT15M"
        assert len({(e["psr_type"], e["direction"]) for e in events}) == 19

    @staticmethod
    def entsoe_doc(series: str) -> str:
        ns = "urn:iec62325.351:tc57wg16:451-6:generationloaddocument:3:0"
        return f'<GL_MarketDocument xmlns="{ns}"><mRID>d</mRID><TimeSeries><mRID>1</mRID>{series}</TimeSeries></GL_MarketDocument>'

    def test_entsoe_consumption_hourly_and_invalid_documents(self) -> None:
        period = "<Period><timeInterval><start>2026-10-13T00:00Z</start></timeInterval><resolution>{r}</resolution>{p}</Period>"
        series = "<outBiddingZone_Domain.mRID>Z</outBiddingZone_Domain.mRID>" + period.format(
            r="PT1H", p="<Point><position>3</position><quantity>5</quantity></Point><Point><position>4</position></Point>"
        )
        events = decode("entsoe", self.entsoe_doc(series))
        assert [(e["direction"], e["area"], e["timestamp"], e["quantity"], e["psr_type"]) for e in events] == [
            ("consumption", "Z", "2026-10-13T02:00Z", 5.0, None),
            ("consumption", "Z", "2026-10-13T03:00Z", None, None),
        ]
        for bad in (period.format(r="P1D", p=""), period.format(r="", p="")):
            with pytest.raises(DecodeError, match="resolution"):
                decode("entsoe", self.entsoe_doc(bad))
        with pytest.raises(DecodeError, match="time"):
            decode("entsoe", self.entsoe_doc("<Period><timeInterval><start>13/10/2026</start></timeInterval></Period>"))
        with pytest.raises(DecodeError, match="invalid XML"):
            decode("entsoe", "<not-closed>")

    def test_entsoe_acknowledgements(self) -> None:
        ack = (
            '<Acknowledgement_MarketDocument xmlns="urn:iec62325.351:tc57wg16:451-1:acknowledgementdocument:7:0">'
            "<Reason><code>999</code><text>{}</text></Reason></Acknowledgement_MarketDocument>"
        )
        assert decode("entsoe", ack.format("No matching data found for Data item ACTUAL_GENERATION")) == []
        with pytest.raises(TransportError, match=r"999 Authentication failed\."):
            decode("entsoe", ack.format("Authentication failed."))
