"""OpenStreetMap minutely replication diffs."""

from __future__ import annotations

import re
from collections.abc import AsyncGenerator, Mapping, Sequence
from html import unescape

from stream_consumers.adapters.outbound.providers.decoders import BaseDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.base import FileDropSource, FileLocation
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import Credentials, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies
from stream_consumers.ports.outbound.system import ClockPort


class OsmChangeDecoder(BaseDecoder):
    """osmChange XML (gzip): one event per node/way/relation, its attributes plus its tags as `tag:<key>`;
    the enclosing action (create/modify/delete) is kept. XML character entities are decoded."""

    ACTION = re.compile(r"<(create|modify|delete)>(.*?)</\1>", re.S)
    ELEMENT = re.compile(r"<(node|way|relation) ([^>]*?)(/>|>(.*?)</\1>)", re.S)
    ATTRIBUTE = re.compile(r'(\w+)="([^"]*)"')
    TAG = re.compile(r'<tag k="([^"]*)" v="([^"]*)"')

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        xml = self.gunzip(self.raw(message)).decode("utf-8", "replace")
        out = []
        for action in self.ACTION.finditer(xml):
            for element in self.ELEMENT.finditer(action.group(2)):
                record: dict[str, object] = {k: unescape(v) for k, v in self.ATTRIBUTE.findall(element.group(2))}
                record.update(element=element.group(1), action=action.group(1))
                record.update({f"tag:{unescape(k)}": unescape(v) for k, v in self.TAG.findall(element.group(4) or "")})
                out.append(record)
        return out


class OsmMinutelySource(FileDropSource):
    """Minutely replication: `state.txt` names the newest sequence; its diff covers one minute."""

    STATE = "https://planet.openstreetmap.org/replication/minute/state.txt"
    DIFF = "https://planet.openstreetmap.org/replication/minute/{a}/{b}/{c}.osc.gz"

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        interval_s: float = 30.0,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, interval_s, backoff)
        self._http = http

    async def _locate(self) -> FileLocation:
        response = await self._http.get(self.STATE)
        match = re.search(rb"sequenceNumber=(\d+)", response.body) if response.status == 200 else None
        if match is None:
            raise TransportError(f"no sequenceNumber in {self.STATE} (HTTP {response.status})")
        seq = f"{int(match.group(1)):09d}"
        return FileLocation(seq, self.DIFF.format(a=seq[0:3], b=seq[3:6], c=seq[6:9]), 60.0)

    async def _read(self, location: FileLocation) -> AsyncGenerator[Mapping[str, object]]:
        response = await self._http.get(location.url)
        if response.status != 200:
            raise TransportError(f"HTTP {response.status} for {location.url}")
        for record in self._decoder.decode(RawMessage(response.body)):
            yield record


class OsmFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="osm",
        name="OpenStreetMap minutely replication diffs",
        category="Internet & software",
        provider="OpenStreetMap Foundation",
        group=Group.KEYLESS,
        delivery=Delivery.FILE_DROP,
        transport=Transport.HTTP,
        endpoint="https://planet.openstreetmap.org/replication/minute/",
        docs_url="https://wiki.openstreetmap.org/wiki/Planet.osm/diffs",
        terms_url="https://www.openstreetmap.org/copyright",
        personal_fields=("user", "uid"),
        notes="One osmChange file per minute; rate = elements in the newest file / 60 s.",
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        return OsmMinutelySource(self.DESCRIPTOR, OsmChangeDecoder(), deps.clock, deps.http)


FACTORY = OsmFactory()
