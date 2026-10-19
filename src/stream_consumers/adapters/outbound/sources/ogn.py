"""Open Glider Network — live positions of gliders, light aircraft and ADS-B traffic (APRS-IS)."""

from __future__ import annotations

import re
from collections.abc import Mapping

from stream_consumers.adapters.outbound.decoders import LineDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.tcp import TcpLineSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class OgnBeaconDecoder(LineDecoder):
    """Aircraft position beacons `CALL>DST,PATH,q..,RECEIVER:/hhmmssh` + position + OGN comment.

    Server comments (`#`), receiver beacons (no `id` token) and status lines are not events. A
    beacon whose `id` token sets the stealth or no-tracking flag is dropped: OGN's data rules ask
    re-distributors to follow the owner's tracking privacy choices.
    """

    POSITION = re.compile(
        r"^(?P<callsign>[^>]+)>(?P<dstcall>[^,:]+),(?P<path>[^:]*):/(?P<time>\d{6})h"
        r"(?P<lat>\d{4}\.\d{2})(?P<ns>[NS])(?P<table>.)(?P<lon>\d{5}\.\d{2})(?P<ew>[EW])(?P<symbol>.)"
        r"(?:(?P<course>\d{3})/(?P<speed>\d{3}))?(?:/A=(?P<altitude>-?\d{6}))?\s*(?P<comment>.*)$"
    )
    TOKENS: tuple[tuple[str, re.Pattern[str], type], ...] = (
        ("climb_rate_fpm", re.compile(r"^([+-]\d+)fpm$"), int),
        ("turn_rate_rot", re.compile(r"^([+-][\d.]+)rot$"), float),
        ("flight_level", re.compile(r"^FL([\d.]+)$"), float),
        ("signal_quality_db", re.compile(r"^([\d.]+)dB$"), float),
        ("error_count", re.compile(r"^(\d+)e$"), int),
        ("frequency_offset_khz", re.compile(r"^([+-][\d.]+)kHz$"), float),
        ("gps_quality", re.compile(r"^gps(\S+)$"), str),
        ("squawk", re.compile(r"^Sq(\d{4})$"), str),
        ("software_version", re.compile(r"^s(\d+\.\d+)$"), str),
        ("hardware_version", re.compile(r"^h([0-9A-Fa-f]+)$"), str),
        ("real_address", re.compile(r"^r([0-9A-Fa-f]{6})$"), str),
        ("flight_id", re.compile(r"^[A-Z]\d:(\S+)$"), str),
    )
    ID = re.compile(r"^id([0-9A-Fa-f]{2})([0-9A-Fa-f]{6})$")
    PRECISION = re.compile(r"^!W(\d)(\d)!$")

    @staticmethod
    def degrees(value: str, whole: int, hemisphere: str, extra: int) -> float:
        minutes = float(value[whole:]) + extra / 1000
        sign = -1 if hemisphere in "SW" else 1
        return round(sign * (int(value[:whole]) + minutes / 60), 6)

    def parse_line(self, line: str, message: RawMessage) -> Mapping[str, object] | None:
        match = self.POSITION.match(line)
        if match is None:
            return None
        tokens = match["comment"].split()
        identity = next((m for m in map(self.ID.match, tokens) if m), None)
        if identity is None:
            return None
        flags = int(identity[1], 16)
        if flags & 0xC0:
            return None
        path = match["path"].split(",")
        precision = next((m for m in map(self.PRECISION.match, tokens) if m), None)
        lat_extra, lon_extra = (int(precision[1]), int(precision[2])) if precision else (0, 0)
        record: dict[str, object] = {
            "callsign": match["callsign"],
            "dstcall": match["dstcall"],
            "receiver": path[-1],
            "relay": ",".join(path[:-1]),
            "timestamp_hhmmss": match["time"],
            "latitude": self.degrees(match["lat"], 2, match["ns"], lat_extra),
            "longitude": self.degrees(match["lon"], 3, match["ew"], lon_extra),
            "symbol": match["table"] + match["symbol"],
            "address": identity[2].upper(),
            "address_type": flags & 0x03,
            "aircraft_type": (flags >> 2) & 0x0F,
        }
        if match["course"] is not None:
            record["course_deg"] = int(match["course"])
            record["ground_speed_kt"] = int(match["speed"])
        if match["altitude"] is not None:
            record["altitude_ft"] = int(match["altitude"])
        other = []
        for token in tokens:
            if token is identity.string or (precision is not None and token is precision.string):
                continue
            for name, pattern, kind in self.TOKENS:
                found = pattern.match(token)
                if found:
                    record[name] = kind(found[1])
                    break
            else:
                other.append(token)
        if other:
            record["other"] = " ".join(other)
        return record


class OgnFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="ogn",
        name="Open Glider Network — live positions of gliders, light aircraft and ADS-B traffic",
        category="Transport",
        provider="Open Glider Network",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.TCP,
        endpoint="aprs://aprs.glidernet.org:14580 (filter r/48/10/3000)",
        docs_url="https://wiki.glidernet.org/wiki:subscribe-to-ogn-data",
        terms_url="https://www.glidernet.org/ogn-data-usage/",
        notes=(
            "Read-only APRS-IS login (callsign N0CALL, passcode -1) with a range filter of 3,000 km around 48°N 10°E "
            "(Europe); an event is an aircraft position beacon. Beacons whose owner chose stealth or no-tracking are "
            "dropped. Data under ODbL; OGN asks not to re-distribute data older than 24 hours."
        ),
    )
    HOST = "aprs.glidernet.org"
    PORT = 14580
    LOGIN = "user N0CALL pass -1 vers stream-consumers 0.1 filter r/48/10/3000"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return TcpLineSource(self.DESCRIPTOR, OgnBeaconDecoder(), deps.clock, self.HOST, self.PORT, greeting=[self.LOGIN])


FACTORY = OgnFactory()
