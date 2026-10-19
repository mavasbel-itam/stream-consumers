"""Kafka consumer source (aiokafka)."""

from __future__ import annotations

from collections.abc import AsyncGenerator, Sequence

from aiokafka import AIOKafkaConsumer

from stream_consumers.adapters.outbound.providers.transports.base import PushEventSource
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import DecoderPort
from stream_consumers.ports.outbound.system import ClockPort


class KafkaSource(PushEventSource):
    """Consumes `topics` from `bootstrap_servers` as consumer group `group_id` (plaintext, no SASL).

    `start_at` is Kafka's auto.offset.reset for a group without committed offsets: "latest" reads
    only what arrives from now on, "earliest" replays what the broker still retains. The message
    key, when present, is passed to the decoder as the `key` attribute (UTF-8 text).
    """

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        bootstrap_servers: str,
        topics: Sequence[str],
        group_id: str,
        start_at: str = "latest",
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        if not topics:
            raise ValueError("topics must not be empty")
        if start_at not in ("latest", "earliest"):
            raise ValueError("start_at must be 'latest' or 'earliest'")
        self._servers = bootstrap_servers
        self._topics = tuple(topics)
        self._group_id = group_id
        self._start_at = start_at

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        consumer = AIOKafkaConsumer(
            *self._topics,
            bootstrap_servers=self._servers,
            group_id=self._group_id,
            auto_offset_reset=self._start_at,
            enable_auto_commit=True,
        )
        await consumer.start()
        try:
            while True:
                record = await consumer.getone()
                attributes = {"topic": record.topic, "partition": str(record.partition), "offset": str(record.offset)}
                if record.key is not None:
                    attributes["key"] = record.key.decode("utf-8", "replace")
                yield RawMessage(record.value or b"", attributes)
        finally:
            await consumer.stop()
