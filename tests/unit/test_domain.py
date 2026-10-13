"""Domain rules: pure functions and value objects."""

from __future__ import annotations

import pytest

from stream_consumers.domain.errors import MissingCredentialError, UnknownSourceError
from stream_consumers.domain.models import RateBasis, RunReport, RunStatus
from stream_consumers.domain.policy import (
    MASK,
    MINIMUM_RATE,
    Backoff,
    ChangeDetector,
    PersonalDataMasker,
    attribute_count,
    flatten,
    median,
    median_rate,
    meets_minimum_rate,
    profile_fields,
    rate,
)


def report(status: RunStatus = RunStatus.OK, value: float | None = 1.0) -> RunReport:
    return RunReport("s", status, 1, 1.0, value, RateBasis.OBSERVED, 1.0, 0.1, 0.0)


class TestFlatten:
    def test_nested_mappings_become_dotted_keys(self) -> None:
        assert flatten({"a": {"b": {"c": 1}}, "d": 2}) == {"a.b.c": 1, "d": 2}

    def test_lists_scalars_and_empty_mappings_are_leaves(self) -> None:
        assert flatten({"a": [1, {"x": 1}], "b": {}, "c": None}) == {"a": [1, {"x": 1}], "b": {}, "c": None}

    def test_attribute_count_counts_leaves(self) -> None:
        assert attribute_count({"a": {"b": 1, "c": 2}, "d": []}) == 3


class TestRateAndMedian:
    def test_rate_rounds_to_three_decimals(self) -> None:
        assert rate(10, 3.0) == 3.333

    @pytest.mark.parametrize("seconds", [0.0, -1.0])
    def test_rate_is_unknown_without_elapsed_time(self, seconds: float) -> None:
        assert rate(10, seconds) is None

    def test_median(self) -> None:
        assert median([3, 1, 2]) == 2.0
        assert median([]) == 0.0


class TestChangeDetector:
    def test_first_snapshot_is_all_new_then_only_changes(self) -> None:
        d = ChangeDetector(["id"], ["v"])
        assert d.changed([{"id": 1, "v": 1}, {"id": 2, "v": 1}]) == [{"id": 1, "v": 1}, {"id": 2, "v": 1}]
        assert d.changed([{"id": 1, "v": 1}, {"id": 2, "v": 2}, {"id": 3, "v": 0}]) == [{"id": 2, "v": 2}, {"id": 3, "v": 0}]

    def test_fields_outside_the_signature_do_not_count(self) -> None:
        d = ChangeDetector(["id"], ["v"])
        d.changed([{"id": 1, "v": 1, "noise": 1}])
        assert d.changed([{"id": 1, "v": 1, "noise": 2}]) == []

    def test_without_signature_the_whole_record_counts(self) -> None:
        d = ChangeDetector(["id"])
        d.changed([{"id": 1, "v": {"a": 1}}])
        assert d.changed([{"id": 1, "v": {"a": 2}}]) == [{"id": 1, "v": {"a": 2}}]

    def test_nested_key_and_signature_fields_use_dotted_names(self) -> None:
        d = ChangeDetector(["k.id"], ["s.t"])
        d.changed([{"k": {"id": 1}, "s": {"t": 1}}])
        assert d.changed([{"k": {"id": 1}, "s": {"t": 2}}]) == [{"k": {"id": 1}, "s": {"t": 2}}]

    def test_a_key_repeated_in_one_snapshot_counts_once(self) -> None:
        """Negative control: duplicates inside one snapshot must not inflate the change count."""
        d = ChangeDetector(["id"], ["v"])
        d.changed([{"id": 1, "v": 0}])
        assert d.changed([{"id": 1, "v": 1}, {"id": 1, "v": 2}]) == [{"id": 1, "v": 2}]

    def test_requires_key_fields(self) -> None:
        with pytest.raises(ValueError):
            ChangeDetector([])


class TestBackoff:
    def test_delays_grow_and_are_capped(self) -> None:
        b = Backoff(initial_s=1, factor=2, max_s=5, max_attempts=4)
        assert [b.delay(n) for n in (1, 2, 3, 4)] == [1, 2, 4, 5]

    def test_allows_up_to_max_attempts(self) -> None:
        b = Backoff(max_attempts=2)
        assert b.allows(2) and not b.allows(3)

    @pytest.mark.parametrize(
        "kwargs",
        [dict(initial_s=0), dict(factor=0.5), dict(initial_s=10, max_s=1), dict(max_attempts=-1)],
    )
    def test_rejects_invalid_parameters(self, kwargs: dict[str, float]) -> None:
        with pytest.raises(ValueError):
            Backoff(**kwargs)  # type: ignore[arg-type]

    def test_attempts_are_one_based(self) -> None:
        with pytest.raises(ValueError):
            Backoff().delay(0)


class TestPersonalDataMasker:
    def test_masks_exact_and_wildcard_fields(self) -> None:
        m = PersonalDataMasker(["user", "actor.*"])
        assert m.mask({"user": "ana", "actor": {"login": "x", "id": 1}, "n": 3}) == {
            "user": MASK,
            "actor.login": MASK,
            "actor.id": MASK,
            "n": 3,
        }

    def test_empty_personal_values_stay_empty(self) -> None:
        assert PersonalDataMasker(["user"]).mask({"user": "", "u": None}) == {"user": "", "u": None}

    def test_scrubs_email_addresses_everywhere(self) -> None:
        masked = PersonalDataMasker().mask({"t": "write to a.b@example.org now", "l": ["c@d.io", {"x": "e@f.mx"}], "n": 1})
        assert masked == {"t": "write to <email> now", "l": ["<email>", {"x": "<email>"}], "n": 1}

    def test_leaks_reports_unmasked_personal_values_and_emails(self) -> None:
        m = PersonalDataMasker(["user"])
        assert m.leaks({"user": "ana", "note": ["x@y.org"], "ok": "fine"}) == ["user", "note"]
        assert m.leaks(m.mask({"user": "ana", "note": ["x@y.org"]})) == []

    def test_is_personal(self) -> None:
        m = PersonalDataMasker(["reply-*"])
        assert m.is_personal("reply-parent-user-id") and not m.is_personal("reply")


class TestInclusionRule:
    def test_threshold_is_one_event_per_second(self) -> None:
        assert MINIMUM_RATE == 1.0

    def test_median_over_successful_measured_runs_only(self) -> None:
        reports = [report(value=0.5), report(value=2.0), report(value=3.0), report(RunStatus.ERROR, None), report(value=None)]
        assert median_rate(reports) == 2.0
        assert meets_minimum_rate(reports)

    def test_below_threshold_is_rejected(self) -> None:
        """Negative control: a median of 0.977 events/s does not meet the rule."""
        assert not meets_minimum_rate([report(value=0.977), report(value=0.98), report(value=5.0)])

    def test_no_measurement_is_rejected(self) -> None:
        assert median_rate([report(RunStatus.NO_EVENTS, 0.0)]) is None
        assert not meets_minimum_rate([])


class TestProfileFields:
    def test_presence_distinct_kinds_and_numeric_range(self) -> None:
        fields = {f.name: f for f in profile_fields([{"a": 1, "b": "x", "c": None}, {"a": 3, "b": "x", "c": True}, {"a": 2.0, "d": [1]}])}
        assert fields["a"].present_ratio == 1.0 and fields["a"].distinct == 3
        assert (fields["a"].minimum, fields["a"].maximum, fields["a"].mean) == (1.0, 3.0, 2.0)
        assert fields["a"].kinds == ("number",)
        assert fields["b"].present_ratio == round(2 / 3, 4) and fields["b"].distinct == 1 and fields["b"].minimum is None
        assert fields["c"].kinds == ("boolean", "null") and fields["c"].present_ratio == round(1 / 3, 4)
        assert fields["d"].kinds == ("list",)

    def test_mapping_kind_and_empty_field(self) -> None:
        fields = {f.name: f for f in profile_fields([{"m": {}, "e": ""}])}
        assert fields["m"].kinds == ("mapping",)
        assert fields["e"].example == "" and fields["e"].present_ratio == 0.0

    def test_personal_examples_are_masked_but_counted(self) -> None:
        fields = {f.name: f for f in profile_fields([{"user": "ana", "t": "mail me@x.org"}], PersonalDataMasker(["user"]))}
        assert fields["user"].example == MASK and fields["user"].distinct == 1
        assert fields["t"].example == "'mail <email>'"


def test_error_messages_name_the_missing_piece() -> None:
    assert "nope" in str(UnknownSourceError("nope"))
    err = MissingCredentialError("K", "https://x")
    assert err.env_var == "K" and "https://x" in str(err)
