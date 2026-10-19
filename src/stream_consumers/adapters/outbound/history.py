"""Sampling rounds read back from the JSON files `JsonReportSink` writes."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path

from stream_consumers.domain.models import RateBasis, RunReport, RunStatus, SamplingRound
from stream_consumers.ports.outbound import SamplingHistoryPort


def _report(document: Mapping[str, object]) -> RunReport:
    fields = dict(document)
    fields["status"] = RunStatus(fields["status"])
    fields["rate_basis"] = RateBasis(fields["rate_basis"])
    return RunReport(**fields)  # type: ignore[arg-type]


class JsonSamplingHistory(SamplingHistoryPort):
    """Every `round-*.json` below a directory (segments of an interrupted run included), by schedule."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def read_rounds(self) -> Sequence[SamplingRound]:
        if not self._directory.is_dir():
            raise ValueError(f"no such reports directory: {self._directory}")
        rounds = []
        for path in self._directory.rglob("round-*.json"):
            document = json.loads(path.read_text(encoding="utf-8"))
            reports = tuple(_report(r) for r in document["reports"])
            rounds.append(SamplingRound(int(document["number"]), float(document["scheduled_at"]), reports))
        return sorted(rounds, key=lambda r: (r.scheduled_at, r.number))
