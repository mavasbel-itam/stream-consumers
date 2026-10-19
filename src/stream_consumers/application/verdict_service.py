"""Median rate and inclusion verdict per source from recorded sampling rounds."""

from __future__ import annotations

from collections.abc import Sequence

from stream_consumers.domain.models import RateVerdict, SamplingRound
from stream_consumers.domain.policy import median_rate, reports_by_source, verdict
from stream_consumers.ports.inbound import JudgeSamplingUseCase


class VerdictService(JudgeSamplingUseCase):
    def verdicts(self, rounds: Sequence[SamplingRound], planned: int, source_ids: Sequence[str] = ()) -> Sequence[RateVerdict]:
        if planned < 1:
            raise ValueError("planned must be at least 1")
        found = reports_by_source(rounds)
        return [
            RateVerdict(s, len(found.get(s, [])), planned, median_rate(found.get(s, [])), verdict(found.get(s, []), planned))
            for s in (source_ids or sorted(found))
        ]
