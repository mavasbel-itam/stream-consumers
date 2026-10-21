"""EarthScope (IRIS) SeedLink real-time seismic waveforms."""

from __future__ import annotations

import asyncio
import struct
from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.providers.decoders import BaseDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.tcp import TcpRecordSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import Credentials, DecoderPort, EventSourcePort, SourceDependencies
from stream_consumers.ports.outbound.system import ClockPort


class MiniSeedHeaderDecoder(BaseDecoder):
    """SeedLink packet = 8-byte `SL` header (6 hex digits of sequence) + 512-byte miniSEED record.
    One event per record: the fixed-header fields (SEED 2.4 manual, chapter 8)."""

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        packet = self.raw(message)
        if packet[:2] != b"SL" or packet[:6] == b"SLINFO" or len(packet) < 56:
            return []
        h = packet[8:]
        return [
            {
                "sequence": packet[2:8].decode("ascii", "replace"),
                "station": h[8:13].decode("ascii", "replace").strip(),
                "location": h[13:15].decode("ascii", "replace").strip(),
                "channel": h[15:18].decode("ascii", "replace"),
                "network": h[18:20].decode("ascii", "replace"),
                "year": struct.unpack(">H", h[20:22])[0],
                "day_of_year": struct.unpack(">H", h[22:24])[0],
                "hour": h[24],
                "minute": h[25],
                "second": h[26],
                "fraction_0001s": struct.unpack(">H", h[28:30])[0],
                "samples": struct.unpack(">H", h[30:32])[0],
                "rate_factor": struct.unpack(">h", h[32:34])[0],
                "rate_multiplier": struct.unpack(">h", h[34:36])[0],
            }
        ]


class SeedLinkSource(TcpRecordSource):
    """SeedLink 3 handshake: HELLO (two reply lines), then STATION / SELECT / DATA per station (each answered
    `OK`), then END starts the data packets."""

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        host: str,
        port: int,
        stations: Sequence[tuple[str, str]],
        channel: str,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, host, port, record_size=520, backoff=backoff)
        self._stations = tuple(stations)
        self._channel = channel

    async def _handshake(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        async def command(text: str, replies: int) -> None:
            writer.write((text + "\r\n").encode())
            await writer.drain()
            for _ in range(replies):
                answer = (await self._timed(reader.readline())).decode("ascii", "replace").strip()
                if answer.startswith("ERROR"):
                    raise TransportError(f"SeedLink refused {text!r}: {answer}")

        await command("HELLO", 2)
        for network, station in self._stations:
            await command(f"STATION {station} {network}", 1)
            await command(f"SELECT {self._channel}", 1)
            await command("DATA", 1)
        writer.write(b"END\r\n")
        await writer.drain()


class SeedlinkFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="seedlink",
        name="EarthScope (IRIS) SeedLink real-time seismic waveforms",
        category="Science & sensors",
        provider="EarthScope Consortium (IRIS DMC)",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.TCP,
        endpoint="seedlink://rtserve.earthscope.org:18000",
        docs_url="https://ds.iris.edu/ds/nodes/dmc/services/seedlink/",
        terms_url="https://ds.iris.edu/ds/nodes/dmc/services/seedlink/",
        notes="12 IU stations, vertical broadband channel BHZ; the rate grows with the stations selected.",
    )
    HOST = "rtserve.earthscope.org"
    STATIONS = tuple(("IU", s) for s in ("ANMO", "TEIG", "HRV", "COLA", "KONO", "MAJO", "PET", "SNZO", "CTAO", "TATO", "PAB", "RSSD"))

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return SeedLinkSource(self.DESCRIPTOR, MiniSeedHeaderDecoder(), deps.clock, self.HOST, 18000, self.STATIONS, "BHZ")


FACTORY = SeedlinkFactory()
