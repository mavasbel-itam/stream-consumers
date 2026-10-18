"""Pure rules shared by every source. No I/O."""

from __future__ import annotations

import fnmatch
import re
import statistics
from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass

from stream_consumers.domain.models import FieldProfile, RunReport, RunStatus


def flatten(payload: Mapping[str, object], prefix: str = "") -> dict[str, object]:
    """Flatten nested mappings into dotted keys; lists and scalars are leaves.

    An empty mapping is kept as a leaf so the attribute it names is still counted.
    """
    out: dict[str, object] = {}
    for key, value in payload.items():
        name = f"{prefix}{key}"
        if isinstance(value, Mapping) and value:
            out.update(flatten(value, f"{name}."))
        else:
            out[name] = value
    return out


def attribute_count(payload: Mapping[str, object]) -> int:
    return len(flatten(payload))


def rate(events: int, seconds: float) -> float | None:
    """Events per second, or None when no time has elapsed."""
    return round(events / seconds, 3) if seconds > 0 else None


def median(values: Sequence[int]) -> float:
    return float(statistics.median(values)) if values else 0.0


class ChangeDetector:
    """Keeps the last signature per record key; reports records that are new or changed.

    Polled feeds return the whole snapshot each time. Only records whose
    signature differs from the previous poll are events. Without
    `signature_fields` the whole record is the signature.
    """

    def __init__(self, key_fields: Sequence[str], signature_fields: Sequence[str] | None = None) -> None:
        if not key_fields:
            raise ValueError("key_fields must not be empty")
        self._key_fields = tuple(key_fields)
        self._signature_fields = tuple(signature_fields) if signature_fields else None
        self._last: dict[Hashable, Hashable] = {}

    def _pick(self, record: Mapping[str, object], fields: Sequence[str]) -> tuple[str, ...]:
        flat = flatten(record)
        return tuple(repr(flat.get(f)) for f in fields)

    def _signature(self, record: Mapping[str, object]) -> Hashable:
        if self._signature_fields is None:
            return repr(sorted(flatten(record).items(), key=lambda kv: kv[0]))
        return self._pick(record, self._signature_fields)

    def changed(self, records: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
        """Records of one snapshot that are new or changed since the previous snapshot.

        A key repeated inside one snapshot counts once (its last record wins), so a
        provider listing one object twice cannot inflate the change count.
        """
        latest: dict[Hashable, Mapping[str, object]] = {}
        for record in records:
            latest[self._pick(record, self._key_fields)] = record
        out = []
        for key, record in latest.items():
            signature = self._signature(record)
            if self._last.get(key) != signature:
                self._last[key] = signature
                out.append(record)
        return out


@dataclass(frozen=True)
class Backoff:
    """Exponential reconnect delays, capped, with a bounded number of attempts."""

    initial_s: float = 1.0
    factor: float = 2.0
    max_s: float = 60.0
    max_attempts: int = 5

    def __post_init__(self) -> None:
        if self.initial_s <= 0 or self.factor < 1 or self.max_s < self.initial_s or self.max_attempts < 0:
            raise ValueError("invalid backoff parameters")

    def delay(self, attempt: int) -> float:
        """Delay before reconnect number `attempt` (1-based)."""
        if attempt < 1:
            raise ValueError("attempt is 1-based")
        return min(self.max_s, self.initial_s * self.factor ** (attempt - 1))

    def allows(self, attempt: int) -> bool:
        return attempt <= self.max_attempts


EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
MASK = "<masked>"


class PersonalDataMasker:
    """Masks personal fields and any e-mail address inside text values.

    `personal_fields` are flattened field names; shell-style wildcards are allowed
    (``payload.*`` masks every field under ``payload``, and ``payload`` itself when its value is a
    list, because `flatten` keeps lists as leaves).
    """

    def __init__(self, personal_fields: Iterable[str] = ()) -> None:
        self._patterns = tuple(personal_fields)

    def is_personal(self, name: str) -> bool:
        return any(fnmatch.fnmatchcase(name, p) or (p.endswith(".*") and name == p[:-2]) for p in self._patterns)

    @staticmethod
    def _has_value(value: object) -> bool:
        return value not in (None, "", MASK) and not (isinstance(value, (list, Mapping)) and not value)

    def _scrub(self, value: object) -> object:
        if isinstance(value, str):
            return EMAIL.sub("<email>", value)
        if isinstance(value, Mapping):
            return {k: self._scrub(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._scrub(v) for v in value]
        return value

    def mask(self, payload: Mapping[str, object]) -> dict[str, object]:
        """Flattened copy of `payload` with personal values replaced by a marker."""
        return {k: (MASK if self.is_personal(k) and self._has_value(v) else self._scrub(v)) for k, v in flatten(payload).items()}

    def leaks(self, payload: Mapping[str, object]) -> list[str]:
        """Field names that still carry an e-mail address or an unmasked personal value."""
        found = []
        for k, v in flatten(payload).items():
            if (self.is_personal(k) and self._has_value(v)) or EMAIL.search(repr(v)):
                found.append(k)
        return found


MINIMUM_RATE = 1.0
"""Inclusion rule of this repository: median measured rate of at least 1 event/s."""


SILENT_STATUSES = frozenset({RunStatus.NO_EVENTS, RunStatus.ERROR})
"""Runs that delivered nothing; they count as 0 events/s, so a source that is often silent or
unreachable cannot pass on its good rounds alone."""


def round_rate(report: RunReport) -> float | None:
    """The rate one run contributes to the median: its measured rate, 0.0 when it delivered nothing,
    None when it measured nothing (key pending, or a successful run without a rate)."""
    if report.status in SILENT_STATUSES:
        return 0.0
    if report.status is RunStatus.OK:
        return report.rate
    return None


def median_rate(reports: Iterable[RunReport]) -> float | None:
    """Median of the per-run rates (`round_rate`); None when no run measured anything."""
    rates = [rate for rate in map(round_rate, reports) if rate is not None]
    return float(statistics.median(rates)) if rates else None


def meets_minimum_rate(reports: Iterable[RunReport], minimum: float = MINIMUM_RATE) -> bool:
    value = median_rate(reports)
    return value is not None and value >= minimum


def _kind(value: object) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int | float):
        return "number"
    if isinstance(value, str):
        return "text"
    if isinstance(value, list | tuple):
        return "list"
    return "mapping"


def profile_fields(
    payloads: Sequence[Mapping[str, object]], masker: PersonalDataMasker | None = None, example_chars: int = 80
) -> tuple[FieldProfile, ...]:
    """Per flattened field: share of events carrying it, distinct values, kinds and numeric range.

    Statistics use the real values; the example value of a personal field is masked.
    """
    flats = [flatten(p) for p in payloads]
    names = sorted({k for f in flats for k in f})
    out = []
    for name in names:
        values = [f[name] for f in flats if name in f]
        present = [v for v in values if v is not None and v != ""]
        numbers = [float(v) for v in present if _kind(v) == "number"]
        kinds = tuple(sorted({_kind(v) for v in values}))
        if not present:
            example = ""
        elif masker is not None and masker.is_personal(name):
            example = MASK
        else:
            example = EMAIL.sub("<email>", repr(present[0]))[:example_chars]
        out.append(
            FieldProfile(
                name=name,
                present_ratio=round(len(present) / len(flats), 4),
                distinct=len({repr(v) for v in present}),
                kinds=kinds,
                minimum=min(numbers) if numbers else None,
                maximum=max(numbers) if numbers else None,
                mean=round(statistics.fmean(numbers), 6) if numbers else None,
                example=example,
            )
        )
    return tuple(out)
