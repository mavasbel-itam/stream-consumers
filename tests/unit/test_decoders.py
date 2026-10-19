"""Generic decoders of the wire formats."""

from __future__ import annotations

import gzip
from collections.abc import Mapping

import pytest
from google.transit import gtfs_realtime_pb2

from stream_consumers.adapters.outbound.providers.decoders import BaseDecoder, CsvDecoder, GtfsRealtimeDecoder, JsonDecoder, LineDecoder
from stream_consumers.domain.errors import DecodeError
from stream_consumers.domain.models import RawMessage


class TestBaseDecoderHelpers:
    def test_text_and_raw_accept_both_body_types(self) -> None:
        assert BaseDecoder.text(RawMessage(b"\xc3\xa9")) == "é"
        assert BaseDecoder.text(RawMessage("é")) == "é"
        assert BaseDecoder.raw(RawMessage("é")) == b"\xc3\xa9"
        assert BaseDecoder.raw(RawMessage(b"x")) == b"x"

    def test_gunzip(self) -> None:
        assert BaseDecoder.gunzip(gzip.compress(b"abc")) == b"abc"

    @pytest.mark.parametrize("data", [b"not gzip", gzip.compress(b"abc")[:-6]])
    def test_gunzip_rejects_bad_data(self, data: bytes) -> None:
        with pytest.raises(DecodeError):
            BaseDecoder.gunzip(data)


class TestJsonDecoder:
    def test_a_mapping_is_one_event(self) -> None:
        assert JsonDecoder().decode(RawMessage('{"a": 1}')) == [{"a": 1}]

    def test_a_list_yields_its_mappings(self) -> None:
        assert JsonDecoder().decode(RawMessage(b'[{"a": 1}, 2, {"b": 2}]')) == [{"a": 1}, {"b": 2}]

    def test_a_scalar_is_no_event(self) -> None:
        assert JsonDecoder().decode(RawMessage("3")) == []

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(DecodeError):
            JsonDecoder().decode(RawMessage("{nope"))


class Upper(LineDecoder):
    def parse_line(self, line: str, message: RawMessage) -> Mapping[str, object] | None:
        return None if line.startswith("#") else {"line": line.upper()}


def test_line_decoder_skips_blank_and_rejected_lines() -> None:
    assert Upper().decode(RawMessage("a\r\n\n  \n# comment\nb")) == [{"line": "A"}, {"line": "B"}]


class TestCsvDecoder:
    def test_header_row(self) -> None:
        assert CsvDecoder().decode(RawMessage("a,b\n1,2\n")) == [{"a": "1", "b": "2"}]

    def test_fieldnames_delimiter_and_gzip(self) -> None:
        body = gzip.compress(b"1\t2\t3\n")
        assert CsvDecoder("\t", ["x", "y"], gzipped=True).decode(RawMessage(body)) == [{"x": "1", "y": "2"}]

    def test_extra_columns_without_a_name_are_dropped(self) -> None:
        assert CsvDecoder(fieldnames=["x"]).decode(RawMessage("1,2,3\n")) == [{"x": "1"}]

    def test_repeated_column_names_get_suffixes(self) -> None:
        assert CsvDecoder().decode(RawMessage("a,sky,sky,sky\n1,FEW,SCT,\n\n")) == [{"a": "1", "sky": "FEW", "sky_2": "SCT", "sky_3": ""}]

    def test_empty_text_has_no_rows(self) -> None:
        assert CsvDecoder().decode(RawMessage("")) == []


class TestGtfsRealtimeDecoder:
    def test_one_event_per_entity_with_the_feed_timestamp(self) -> None:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.header.gtfs_realtime_version = "2.0"
        feed.header.timestamp = 1700000000
        entity = feed.entity.add()
        entity.id = "v1"
        entity.vehicle.vehicle.id = "bus-7"
        assert GtfsRealtimeDecoder().decode(RawMessage(feed.SerializeToString())) == [
            {"id": "v1", "vehicle": {"vehicle": {"id": "bus-7"}}, "feedTimestamp": 1700000000}
        ]

    def test_garbage_raises(self) -> None:
        with pytest.raises(DecodeError):
            GtfsRealtimeDecoder().decode(RawMessage(b"\xff\xff\xff\xff"))
