"""Reverse Beacon Network (CW/RTTY skimmer spots)."""

from __future__ import annotations

import re
from collections.abc import Mapping

from stream_consumers.adapters.outbound.decoders import LineDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.tcp import TcpLineSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound import EventSourcePort, SourceDependencies


class RbnSpotDecoder(LineDecoder):
    """Telnet spot lines `DX de <spotter>: <kHz> <dx> <mode> <snr> dB <speed> WPM|BPS <type> <hhmm>Z`."""

    SPOT = re.compile(r"DX de (\S+):\s+([\d.]+)\s+(\S+)\s+(\S+)\s+(-?\d+) dB\s+(\d+) (WPM|BPS)\s+(.+?)\s+(\d{4})Z")
    NAMES = ("spotter", "freq", "dx", "mode", "snr", "speed", "unit", "type", "time")

    def parse_line(self, line: str, message: RawMessage) -> Mapping[str, object] | None:
        match = self.SPOT.match(line)
        return dict(zip(self.NAMES, match.groups(), strict=False)) if match else None


class RbnFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="rbn",
        name="Reverse Beacon Network (CW/RTTY skimmer spots)",
        category="Science & sensors",
        provider="Reverse Beacon Network",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.TCP,
        endpoint="telnet://telnet.reversebeacon.net:7000",
        docs_url="https://www.reversebeacon.net/",
        terms_url="https://www.reversebeacon.net/",
        personal_fields=("spotter", "dx"),
        notes="Telnet login asks for a callsign; N0CALL (the conventional placeholder) is sent.",
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return TcpLineSource(self.DESCRIPTOR, RbnSpotDecoder(), deps.clock, "telnet.reversebeacon.net", 7000, greeting=["N0CALL"])


FACTORY = RbnFactory()
