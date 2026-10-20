"""NATS push source."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import nats
import nats.errors

from stream_consumers.adapters.outbound.providers.transports.base import PushEventSource
from stream_consumers.domain.errors import TransportError
from stream_consumers.domain.models import RawMessage, SourceDescriptor
from stream_consumers.domain.policy import Backoff
from stream_consumers.ports.outbound.providers import DecoderPort
from stream_consumers.ports.outbound.system import ClockPort


class NatsSource(PushEventSource):
    """Subscribes to one subject; the message attribute ``subject`` carries the subject.

    The client's own reconnection is disabled so that a lost connection (the
    client raises ConnectionClosedError) or a silence longer than `silence_s`
    reaches the source's back-off instead.
    """

    def __init__(
        self,
        descriptor: SourceDescriptor,
        decoder: DecoderPort,
        clock: ClockPort,
        server: str,
        subject: str,
        user: str | None = None,
        password: str | None = None,
        silence_s: float = 120.0,
        poll_s: float = 1.0,
        backoff: Backoff | None = None,
    ) -> None:
        super().__init__(descriptor, decoder, clock, backoff)
        self._server = server
        self._subject = subject
        self._user = user
        self._password = password
        self._silence_s = silence_s
        self._poll_s = poll_s

    async def _connect(self) -> AsyncGenerator[RawMessage]:
        async def reported_by_the_exception(error: Exception) -> None:  # instead of nats-py's own error log
            return None

        # nats-py retries a first connection forever when max_reconnect_attempts is 0 (it gives up only
        # when the limit is above 0); with 1 an unreachable server raises NoServersError after two tries
        client = await nats.connect(
            servers=[self._server],
            user=self._user,
            password=self._password,
            connect_timeout=20,
            allow_reconnect=False,
            max_reconnect_attempts=1,
            reconnect_time_wait=0.1,
            error_cb=reported_by_the_exception,
        )
        try:
            subscription = await client.subscribe(self._subject)
            silent = 0.0
            while True:
                try:
                    msg = await subscription.next_msg(timeout=self._poll_s)
                except nats.errors.TimeoutError:
                    silent += self._poll_s
                    if silent >= self._silence_s:
                        raise TransportError(f"no NATS message for {self._silence_s} s on {self._subject}") from None
                    continue
                silent = 0.0
                yield RawMessage(msg.data, {"subject": msg.subject})
        finally:
            await client.close()
