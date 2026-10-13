"""The source catalog: descriptors, factories and decoders, checked against real captured messages."""

from __future__ import annotations

import importlib
import json
import struct
from collections.abc import Mapping

import pytest

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources import FACTORIES
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.base import DecodingEventSource, MergedEventSource
from stream_consumers.domain.errors import MissingCredentialError
from stream_consumers.domain.models import Credential, Group, RawMessage
from stream_consumers.domain.policy import PersonalDataMasker
from stream_consumers.ports.outbound import DecoderPort, EventSourcePort, SourceDependencies
from tests.support import ScriptedSource, deps, descriptor, messages

BY_ID = {f.descriptor.id: f for f in FACTORIES}


def module(source_id: str):  # type: ignore[no-untyped-def]
    return importlib.import_module(f"stream_consumers.adapters.outbound.sources.{source_id}")


def decoder_of(source_id: str) -> DecoderPort:
    source = BY_ID[source_id].create(deps())
    if isinstance(source, MergedEventSource):
        source = source._children[0]
    assert isinstance(source, DecodingEventSource)
    return source._decoder


class TestCatalog:
    def test_54_sources_in_three_groups(self) -> None:
        groups = [f.descriptor.group for f in FACTORIES]
        assert len(FACTORIES) == 54 == len(BY_ID)
        assert (groups.count(Group.KEYLESS), groups.count(Group.PROJECT_DOCUMENT), groups.count(Group.FREE_KEY)) == (45, 6, 3)

    def test_project_document_sources(self) -> None:
        assert {f.descriptor.id for f in FACTORIES if f.descriptor.group is Group.PROJECT_DOCUMENT} == {
            "bluesky",
            "wikimedia",
            "gdelt",
            "binance",
            "mempool",
            "opensky",
        }

    @pytest.mark.parametrize("source_id", sorted(BY_ID))
    def test_descriptor_matches_its_module(self, source_id: str) -> None:
        d = BY_ID[source_id].descriptor
        assert module(source_id).FACTORY is BY_ID[source_id]
        assert d.docs_url.startswith("https://") and d.terms_url.startswith("https://")
        assert d.name and d.category and d.provider and d.endpoint
        assert all(isinstance(p, str) and p for p in d.personal_fields)

    @pytest.mark.parametrize("source_id", sorted(BY_ID))
    def test_factory_builds_a_source_without_keys(self, source_id: str) -> None:
        source = BY_ID[source_id].create(deps())
        assert isinstance(source, EventSourcePort)
        assert source.descriptor is BY_ID[source_id].descriptor


class _Keyed(BaseSourceFactory):
    DESCRIPTOR = descriptor("keyed", credential=Credential("K", "https://sign.up"))

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return ScriptedSource(self.DESCRIPTOR, [{"key": key}], deps.clock)  # type: ignore[arg-type]


class TestCredentials:
    def test_required_key_missing_raises(self) -> None:
        with pytest.raises(MissingCredentialError) as error:
            _Keyed().create(deps())
        assert error.value.env_var == "K"

    def test_required_key_present_is_passed(self) -> None:
        assert _Keyed().create(deps(secrets={"K": "abc"}))._payloads == [{"key": "abc"}]  # type: ignore[attr-defined]

    def test_mbta_key_switches_header_and_interval(self) -> None:
        keyless = BY_ID["mbta_v3"].create(deps())
        keyed = BY_ID["mbta_v3"].create(deps(secrets={"MBTA_API_KEY": "k"}))
        assert (keyless._interval_s, keyless._headers) == (20.0, {})  # type: ignore[attr-defined]
        assert (keyed._interval_s, keyed._headers) == (5.0, {"x-api-key": "k"})  # type: ignore[attr-defined]

    def test_tfl_key_goes_in_the_query(self) -> None:
        assert BY_ID["tfl"].create(deps())._urls == ("https://api.tfl.gov.uk/Mode/tube/Arrivals",)  # type: ignore[attr-defined]
        assert BY_ID["tfl"].create(deps(secrets={"TFL_APP_KEY": "k"}))._urls == (  # type: ignore[attr-defined]
            "https://api.tfl.gov.uk/Mode/tube/Arrivals?app_key=k",
        )


# Events per captured message. A 0 is a captured control frame (subscription answer, heartbeat) that
# must not count as an event. Sources read from files or several endpoints are tested in the component tier.
EXPECTED = {
    "adsb_fi": [3],
    "adsb_lol": [3],
    "albion": [1, 1, 1],
    "atlas": [0, 1, 1, 1, 1],
    "base_logs": [0, 1, 1, 1, 1],
    "bicing": [3],
    "binance": [1, 1, 1, 1],
    "bitfinex": None,
    "bitso": [0, 1, 1, 1, 1],
    "bitstamp": [0, 1, 1, 1, 1],
    "bluesky": [1, 1, 1, 1],
    "bsc_logs": [0, 1, 1, 1, 1],
    "bybit": [0, 1, 1, 1, 1],
    "coinbase": [0, 1, 1, 1, 1],
    "crossref": [3],
    "deribit": [0, 1, 1, 1, 1],
    "dt_marine": [1, 1, 1, 1],
    "dt_rail": [1, 1, 1, 1],
    "dt_rail_trains": [1, 1, 1, 1],
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
    "mta_gtfsrt": [3],
    "ndov": [67, 66, 54, 119],
    "npm": [3],
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
    "atlas",
    "base_logs",
    "binance",
    "bitso",
    "bitstamp",
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
    "npm",
    "okx",
    "opensky",
    "polymarket",
    "ris",
    "solana",
    "sensorcomm",
    "usgs_water",
    "xrpl",
    "bicing",
    "adsb_fi",
    "bitfinex",
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

    def test_gemini_update_without_events(self) -> None:
        assert decode("gemini", {"type": "update"}) == []

    def test_plain_json_sources_keep_every_mapping(self) -> None:
        for source_id in ("pskreporter", "wikimedia", "tfl"):
            assert isinstance(decoder_of(source_id), JsonDecoder)
            assert decode(source_id, [{"a": 1}]) == [{"a": 1}]
