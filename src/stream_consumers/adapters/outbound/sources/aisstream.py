"""aisstream.io — global AIS ship positions and static data (free key)."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from stream_consumers.adapters.outbound.decoders import JsonDecoder
from stream_consumers.adapters.outbound.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Credential, Delivery, Group, RawMessage, Setting, SourceDescriptor, Transport
from stream_consumers.ports.outbound import Credentials, EventSourcePort, SourceDependencies


class AisStreamDecoder(JsonDecoder):
    """`{"MessageType": T, "MetaData": {...}, "Message": {T: {...}}}`: one event per AIS message,
    the typed body with the message type and the MetaData added. The SubscriptionConfirmation is not an event."""

    def extract(self, document: object, message: RawMessage) -> Sequence[Mapping[str, object]]:
        if not isinstance(document, Mapping):
            return []
        kind = document.get("MessageType")
        bodies = document.get("Message")
        body = bodies.get(kind) if isinstance(bodies, Mapping) and isinstance(kind, str) else None
        if kind == "SubscriptionConfirmation" or not isinstance(body, Mapping):
            return []
        meta = document.get("MetaData")
        return [{**body, "MessageType": kind, "MetaData": dict(meta) if isinstance(meta, Mapping) else {}}]


def bounding_boxes(text: str) -> list[object]:
    """`[[[lat, lon], [lat, lon]], ...]`, as aisstream.io's subscription expects."""
    boxes = json.loads(text)
    valid = (
        isinstance(boxes, list)
        and boxes
        and all(isinstance(b, list) and len(b) == 2 and all(isinstance(c, list) and len(c) == 2 for c in b) for b in boxes)
    )
    if not valid:
        raise ValueError("AISSTREAM_BOUNDING_BOXES must look like [[[lat1, lon1], [lat2, lon2]], ...]")
    return boxes


class AisStreamFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="aisstream",
        name="aisstream.io — global AIS ship positions and static data",
        category="Transport",
        provider="aisstream.io",
        group=Group.PROJECT_DOCUMENT,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://stream.aisstream.io/v0/stream",
        docs_url="https://aisstream.io/documentation",
        terms_url="https://aisstream.io/privacypolicy",
        credential=Credential(
            ("AISSTREAM_API_KEY",),
            "https://aisstream.io/account",
            how_to_get="Sign in with GitHub on the Account page and create an API key (shown once; server-side use only).",
        ),
        settings=(
            Setting(
                "AISSTREAM_BOUNDING_BOXES",
                "[[[-90, -180], [90, 180]]]",
                "JSON list of boxes, each two [latitude, longitude] corners (default: the whole world).",
            ),
        ),
        notes=(
            "Listed in the project document. The subscription (key + boxes) is sent right after connecting; the "
            "server closes connections without a valid subscription within 3 seconds. Limits: 3 connections per "
            "account and per IP, frames dropped for slow readers. No terms of use are published (only a privacy "
            "policy)."
        ),
    )
    URL = "wss://stream.aisstream.io/v0/stream"

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        subscription = {
            "APIKey": (credentials or {})["AISSTREAM_API_KEY"],
            "BoundingBoxes": bounding_boxes(self.setting(deps, "AISSTREAM_BOUNDING_BOXES")),
        }
        return WebSocketSource(self.DESCRIPTOR, AisStreamDecoder(), deps.clock, self.URL, [subscription])


FACTORY = AisStreamFactory()
