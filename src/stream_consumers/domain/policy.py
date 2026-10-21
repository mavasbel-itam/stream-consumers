"""Pure rules shared by every source. No I/O."""

from __future__ import annotations

import datetime as dt
import fnmatch
import itertools
import json
import math
import re
import statistics
from collections.abc import Hashable, Iterable, Mapping, Sequence
from dataclasses import dataclass

from stream_consumers.domain.models import (
    FieldClass,
    FieldProfile,
    RunReport,
    RunStatus,
    SamplingRound,
    SourceProfile,
    Verdict,
)


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


def finite_numbers(value: object) -> object:
    """`value` with every NaN or infinite float written as None: JSON has no such numbers (RFC 8259 section 6),
    and the null JavaScript's JSON.stringify writes for them keeps every output valid JSON. Tuples become lists."""
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {key: finite_numbers(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [finite_numbers(item) for item in value]
    return value


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


def reports_by_source(rounds: Iterable[SamplingRound]) -> dict[str, list[RunReport]]:
    """Each source's reports across `rounds`, in round order."""
    found: dict[str, list[RunReport]] = {}
    for sampling_round in rounds:
        for report in sampling_round.reports:
            found.setdefault(report.source_id, []).append(report)
    return found


def verdict(reports: Sequence[RunReport], planned: int, minimum: float = MINIMUM_RATE) -> Verdict:
    """Whether the median over `planned` rounds is already on one side of `minimum`, given the
    rounds measured so far. Each missing round may add 0 events/s, any higher rate, or nothing
    (key pending); adding a value never moves the median past that value, so the lowest possible
    median fills every missing round with 0 and the highest with an unbounded rate."""
    if planned < 1:
        raise ValueError("planned must be at least 1")
    rates = [rate for rate in map(round_rate, reports) if rate is not None]
    missing = planned - len(reports)
    if missing <= 0:
        return Verdict.PASSES if meets_minimum_rate(reports, minimum) else Verdict.FAILS
    if statistics.median([*rates, *[0.0] * missing]) >= minimum:
        return Verdict.PASSES
    if statistics.median([*rates, *[math.inf] * missing]) < minimum:
        return Verdict.FAILS
    return Verdict.OPEN


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


ISO_8601 = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$")
NUMERIC_TEXT = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
LEADING_ZERO = re.compile(r"^[+-]?0\d")
"""Digits with a leading zero ("0123", "053306") are codes, not numbers."""
COMPACT_DATE = re.compile(r"^\d{8}(\d{6})?$")
EPOCH_UNITS = (1.0, 1e3, 1e6, 1e9)
"""Seconds, milliseconds, microseconds and nanoseconds since 1970-01-01 UTC."""
EPOCH_WINDOW_S = 400 * 86400
"""An epoch number counts as a time only within this distance of the observation, so counters and
identifiers that happen to be large numbers are not taken for times."""
LATITUDE = frozenset({"lat", "latitude"})
LONGITUDE = frozenset({"lon", "lng", "long", "longitude"})
FREE_TEXT_CHARS = 30
NATURAL_KEY_CANDIDATES = 20
NATURAL_KEY_MAX_FIELDS = 3
NATURAL_KEY_PREFERENCE = (
    FieldClass.IDENTIFIER,
    FieldClass.DATETIME,
    FieldClass.LABEL,
    FieldClass.CATEGORY,
    FieldClass.NUMBER,
    FieldClass.GEOGRAPHIC,
    FieldClass.FREE_TEXT,
)


def category_limit(events: int) -> int:
    """Most distinct values a category may have: max(20, 5 % of the events, rounded up)."""
    return max(20, math.ceil(0.05 * events))


def _number(value: object) -> float | None:
    if _kind(value) == "number":
        return float(value)  # type: ignore[arg-type]
    if isinstance(value, str) and NUMERIC_TEXT.match(value) and not LEADING_ZERO.match(value):
        return float(value)
    return None


def _near(moment: float, observed_at: float) -> bool:
    return abs(moment - observed_at) <= EPOCH_WINDOW_S


def _compact_date(value: object, observed_at: float) -> bool:
    text = str(value) if isinstance(value, str) or _kind(value) == "number" else ""
    if not COMPACT_DATE.match(text):
        return False
    try:
        moment = dt.datetime.strptime(text, "%Y%m%d%H%M%S" if len(text) == 14 else "%Y%m%d").replace(tzinfo=dt.UTC)
    except ValueError:
        return False
    return _near(moment.timestamp(), observed_at)


def _is_epoch(numbers: Sequence[float], observed_at: float | None) -> bool:
    if observed_at is None:
        return False
    return any(all(_near(n / unit, observed_at) for n in numbers) for unit in EPOCH_UNITS)


def _partner(name: str, names: frozenset[str], wanted: frozenset[str]) -> bool:
    prefix = name[: len(name) - len(name.rsplit(".", 1)[-1])]
    return any(other.startswith(prefix) and other[len(prefix) :].lower() in wanted for other in names if "." not in other[len(prefix) :])


def _geographic(name: str, numbers: Sequence[float], names: frozenset[str]) -> bool:
    leaf = name.rsplit(".", 1)[-1].lower()
    if leaf in LATITUDE:
        return all(-90 <= n <= 90 for n in numbers) and _partner(name, names, LONGITUDE)
    if leaf in LONGITUDE:
        return all(-180 <= n <= 180 for n in numbers) and _partner(name, names, LATITUDE)
    return False


def classify_field(
    name: str, present: Sequence[object], events: int, names: frozenset[str], observed_at: float | None
) -> tuple[FieldClass, bool]:
    """The field's class and whether its numbers are carried as text; rules apply in `FieldClass` order.

    `present` are the field's non-empty values, `events` the sample size, `names` every field of the
    sample (to find a coordinate's partner) and `observed_at` the epoch second of the observation.
    """
    if not present:
        return FieldClass.EMPTY, False
    kinds = {_kind(v) for v in present}
    if kinds == {"text"} and all(ISO_8601.match(v) for v in present):  # type: ignore[arg-type]
        return FieldClass.DATETIME, False
    if observed_at is not None and kinds <= {"number", "text"} and all(_compact_date(v, observed_at) for v in present):
        return FieldClass.DATETIME, False
    numbers = [_number(v) for v in present]
    if None not in numbers and kinds <= {"number", "text"}:
        values = [n for n in numbers if n is not None]
        as_text = "text" in kinds
        if _is_epoch(values, observed_at):
            return FieldClass.DATETIME, False
        if _geographic(name, values, names):
            return FieldClass.GEOGRAPHIC, as_text
        return FieldClass.NUMBER, as_text
    distinct = len({repr(v) for v in present})
    if kinds == {"text"}:
        texts = [str(v) for v in present]
        spaced = sum(" " in t for t in texts)
        if spaced == 0 and distinct > category_limit(events):
            return FieldClass.IDENTIFIER, False
        if statistics.fmean(map(len, texts)) >= FREE_TEXT_CHARS and 2 * distinct >= len(texts) and 2 * spaced >= len(texts):
            return FieldClass.FREE_TEXT, False
        if distinct > category_limit(events):
            return FieldClass.LABEL, False
    if kinds <= {"text", "boolean"} and distinct <= category_limit(events):
        return FieldClass.CATEGORY, False
    return FieldClass.NESTED, False


def profile_fields(
    payloads: Sequence[Mapping[str, object]],
    masker: PersonalDataMasker | None = None,
    example_chars: int = 80,
    observed_at: float | None = None,
) -> tuple[FieldProfile, ...]:
    """Per flattened field: share of events carrying it, distinct values, kinds, numeric range and class.

    Statistics use the real values; the example value of a personal field is masked.
    """
    flats = [flatten(p) for p in payloads]
    names = sorted({k for f in flats for k in f})
    every = frozenset(names)
    out = []
    for name in names:
        values = [f[name] for f in flats if name in f]
        present = [v for v in values if v is not None and v != ""]
        numbers = [float(v) for v in present if _kind(v) == "number"]
        kinds = tuple(sorted({_kind(v) for v in values}))
        field_class, numeric_text = classify_field(name, present, len(flats), every, observed_at)
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
                field_class=field_class,
                numeric_text=numeric_text,
            )
        )
    return tuple(out)


def _canonical(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"), default=str)


def natural_key(payloads: Sequence[Mapping[str, object]], fields: Sequence[FieldProfile]) -> tuple[str, ...]:
    """Smallest set of fields (at most 3) whose values are unique across the sample.

    Candidates are the fields present in every event whose class is neither nested nor empty,
    ordered by class (`NATURAL_KEY_PREFERENCE`: identifiers and times before measurements, so a
    coordinate pair that happens to be unique is not taken for a key), then by distinct values and
    name; the first 20 are tried, smaller sets first.
    Empty when the sample has fewer than 2 events or no such set exists (identical events included).
    """
    if len(payloads) < 2:
        return ()
    flats = [flatten(p) for p in payloads]
    usable = [f for f in fields if f.present_ratio == 1.0 and f.field_class in NATURAL_KEY_PREFERENCE]
    ordered = sorted(usable, key=lambda f: (NATURAL_KEY_PREFERENCE.index(f.field_class), -f.distinct, f.name))
    candidates = [f.name for f in ordered[:NATURAL_KEY_CANDIDATES]]
    for size in range(1, NATURAL_KEY_MAX_FIELDS + 1):
        for combo in itertools.combinations(candidates, size):
            if len({tuple(repr(flat[n]) for n in combo) for flat in flats}) == len(flats):
                return combo
    return ()


def profile_sample(run: RunReport, payloads: Sequence[Mapping[str, object]], masker: PersonalDataMasker | None = None) -> SourceProfile:
    """Everything `profile` reports about one source's sample; times are judged against the run's start."""
    fields = profile_fields(payloads, masker, observed_at=run.started_at)
    if not payloads:
        return SourceProfile(run, 0, fields, None, None, None, ())
    canonical = [_canonical(p) for p in payloads]
    sizes = sorted(len(c.encode("utf-8")) for c in canonical)
    return SourceProfile(
        run=run,
        events_inspected=len(payloads),
        fields=fields,
        bytes_mean=round(statistics.fmean(sizes), 1),
        bytes_p95=sizes[math.ceil(0.95 * len(sizes)) - 1],
        duplicate_ratio=round(1 - len(set(canonical)) / len(canonical), 4),
        natural_key=natural_key(payloads, fields),
    )
