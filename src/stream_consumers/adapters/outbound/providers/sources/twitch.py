"""Twitch chat (anonymous read-only IRC)."""

from __future__ import annotations

from collections.abc import Mapping

from stream_consumers.adapters.outbound.providers.decoders import LineDecoder
from stream_consumers.adapters.outbound.providers.sources._base import BaseSourceFactory
from stream_consumers.adapters.outbound.providers.transports.websocket import WebSocketSource
from stream_consumers.domain.models import Delivery, Group, RawMessage, SourceDescriptor, Transport
from stream_consumers.ports.outbound.providers import Credentials, EventSourcePort, SourceDependencies


class TwitchChatDecoder(LineDecoder):
    """IRCv3 `PRIVMSG` lines with tags: the tags, the channel and the message text become one event."""

    def parse_line(self, line: str, message: RawMessage) -> Mapping[str, object] | None:
        if not (line.startswith("@") and " PRIVMSG " in line):
            return None
        tag_part = line[1:].split(" ", 1)[0]
        event: dict[str, object] = dict(kv.split("=", 1) for kv in tag_part.split(";") if "=" in kv)
        event["channel"] = line.split(" PRIVMSG ", 1)[1].split(" ", 1)[0]
        event["message"] = line.split(" :", 2)[-1]
        return event


class TwitchFactory(BaseSourceFactory):
    DESCRIPTOR = SourceDescriptor(
        id="twitch",
        name="Twitch chat (anonymous read-only IRC)",
        category="Games, media & social",
        provider="Twitch Interactive",
        group=Group.KEYLESS,
        delivery=Delivery.PUSH,
        transport=Transport.WEBSOCKET,
        endpoint="wss://irc-ws.chat.twitch.tv:443",
        docs_url="https://dev.twitch.tv/docs/chat/irc/",
        terms_url="https://legal.twitch.com/legal/developer-agreement/",
        personal_fields=("display-name", "user-id", "id", "client-nonce", "message", "reply-*", "room-id"),
        notes="Anonymous read-only login (justinfan nick) to 12 large Spanish- and English-language channels. Chat contains personal content.",
    )
    URL = "wss://irc-ws.chat.twitch.tv:443"
    CHANNELS = (
        "ibai",
        "elxokas",
        "auronplay",
        "rivers_gg",
        "kaicenat",
        "xqc",
        "caseoh_",
        "jynxzi",
        "zackrawrr",
        "tarik",
        "elspreen",
        "juansguarnizo",
    )

    def _build(self, deps: SourceDependencies, credentials: Credentials | None) -> EventSourcePort:
        login = ["CAP REQ :twitch.tv/tags", "PASS SCHMOOPIIE", "NICK justinfan48213", "JOIN " + ",".join("#" + c for c in self.CHANNELS)]
        return WebSocketSource(
            self.DESCRIPTOR,
            TwitchChatDecoder(),
            deps.clock,
            self.URL,
            login,
            replies={"PING": "PONG :tmi.twitch.tv"},
            split_lines=True,
        )


FACTORY = TwitchFactory()
