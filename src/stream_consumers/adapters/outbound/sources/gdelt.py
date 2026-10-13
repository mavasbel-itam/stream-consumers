"""GDELT 2.0 Event Database — 15-minute event exports."""

from __future__ import annotations

import io
import zipfile
from collections.abc import AsyncGenerator, Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import CsvDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.base import FileDropSource, FileLocation
from stream_consumers.domain.errors import DecodeError, TransportError
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound import ClockPort, DecoderPort, EventSourcePort, HttpClientPort, SourceDependencies

GDELT_EVENT_FIELDS = (
    "GlobalEventID",
    "Day",
    "MonthYear",
    "Year",
    "FractionDate",
    *(
        f"{actor}{f}"
        for actor in ("Actor1", "Actor2")
        for f in (
            "Code",
            "Name",
            "CountryCode",
            "KnownGroupCode",
            "EthnicCode",
            "Religion1Code",
            "Religion2Code",
            "Type1Code",
            "Type2Code",
            "Type3Code",
        )
    ),
    "IsRootEvent",
    "EventCode",
    "EventBaseCode",
    "EventRootCode",
    "QuadClass",
    "GoldsteinScale",
    "NumMentions",
    "NumSources",
    "NumArticles",
    "AvgTone",
    *(
        f"{prefix}Geo_{f}"
        for prefix in ("Actor1", "Actor2", "Action")
        for f in ("Type", "Fullname", "CountryCode", "ADM1Code", "ADM2Code", "Lat", "Long", "FeatureID")
    ),
    "DATEADDED",
    "SOURCEURL",
)
"""The 61 columns of the GDELT 2.0 event export, in order, as named in the GDELT Event Codebook V2.0."""


class GdeltExportDecoder(CsvDecoder):
    """Zip archive holding one tab-separated file without header."""

    def __init__(self) -> None:
        super().__init__(delimiter="\t", fieldnames=GDELT_EVENT_FIELDS)

    def decode(self, message: RawMessage) -> Sequence[Mapping[str, object]]:
        try:
            with zipfile.ZipFile(io.BytesIO(self.raw(message))) as archive:
                inner = archive.read(archive.namelist()[0])
        except (zipfile.BadZipFile, IndexError) as exc:
            raise DecodeError(f"not a GDELT export archive: {exc}") from exc
        return super().decode(RawMessage(inner))


class GdeltExportSource(FileDropSource):
    """`lastupdate.txt` lists the newest 15-minute files; the first line is the event export."""

    LAST_UPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        http: HttpClientPort,
        interval_s: float = 120.0,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, interval_s, backoff)
        self._http = http

    async def _locate(self) -> FileLocation:
        response = await self._http.get(self.LAST_UPDATE)
        lines = response.body.decode("utf-8", "replace").split("\n") if response.status == 200 else []
        url = next((line.split()[2] for line in lines if line.endswith(".export.CSV.zip") and len(line.split()) == 3), None)
        if url is None:
            raise TransportError(f"no event export listed in {self.LAST_UPDATE} (HTTP {response.status})")
        return FileLocation(url.rsplit("/", 1)[1], url, 900.0)

    async def _read(self, location: FileLocation) -> AsyncGenerator[Mapping[str, object]]:
        response = await self._http.get(location.url)
        if response.status != 200:
            raise TransportError(f"HTTP {response.status} for {location.url}")
        for record in self._decoder.decode(RawMessage(response.body)):
            yield record


class GdeltFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="gdelt",
        name="GDELT 2.0 Event Database — 15-minute event exports",
        category="Games, media & social",
        provider="The GDELT Project",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.FILE_DROP,
        transport=Transport.HTTP,
        endpoint="http://data.gdeltproject.org/gdeltv2/lastupdate.txt",
        docs_url="https://www.gdeltproject.org/data.html",
        terms_url="https://www.gdeltproject.org/about.html",
        notes="One event export every 15 minutes; rate = rows in the newest export / 900 s. Measured median 0.977 events/s, kept because the project document lists it. Column names: https://data.gdeltproject.org/documentation/GDELT-Event_Codebook-V2.0.pdf",
    )

    def _build(self, deps: SourceDependencies, key: str | None) -> EventSourcePort:
        return GdeltExportSource(self.DESCRIPTOR, GdeltExportDecoder(), deps.clock, deps.http)


FACTORY = GdeltFactory()
