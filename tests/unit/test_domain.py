"""Domain rules: pure functions and value objects."""

from __future__ import annotations

import pytest

from stream_consumers.domain.errors import MissingCredentialError, UnknownSourceError
from stream_consumers.domain.models import FieldClass, FieldProfile, Group, RateBasis, RunReport, RunStatus, SamplingRound, Verdict
from stream_consumers.domain.policy import (
    MASK,
    MINIMUM_RATE,
    Backoff,
    ChangeDetector,
    PersonalDataMasker,
    attribute_count,
    category_limit,
    classify_field,
    flatten,
    median,
    median_rate,
    meets_minimum_rate,
    natural_key,
    profile_fields,
    profile_sample,
    rate,
    reports_by_source,
    round_rate,
    verdict,
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

    def test_a_wildcard_also_masks_a_list_under_its_prefix(self) -> None:
        # flatten keeps lists as leaves, so "mentions.*" must also cover the list "mentions" itself
        m = PersonalDataMasker(["mentions.*"])
        event = {"mentions": [{"acct": "ana@example.social", "username": "ana"}], "id": "1"}
        assert m.leaks(event) == ["mentions"]
        assert m.mask(event) == {"mentions": MASK, "id": "1"} and m.leaks(m.mask(event)) == []
        assert m.mask({"mentions": [], "m": {}}) == {"mentions": [], "m": {}}
        assert not m.is_personal("mentionsx") and not m.is_personal("id")

    def test_empty_containers_are_not_leaks(self) -> None:
        assert PersonalDataMasker(["account.*", "tags"]).leaks({"account": {}, "tags": []}) == []

    def test_is_personal(self) -> None:
        m = PersonalDataMasker(["reply-*"])
        assert m.is_personal("reply-parent-user-id") and not m.is_personal("reply")


class TestInclusionRule:
    def test_threshold_is_one_event_per_second(self) -> None:
        assert MINIMUM_RATE == 1.0

    def test_each_status_contributes_its_own_rate(self) -> None:
        assert round_rate(report(value=2.5)) == 2.5
        assert round_rate(report(RunStatus.NO_EVENTS, None)) == 0.0
        assert round_rate(report(RunStatus.ERROR, None)) == 0.0
        assert round_rate(report(RunStatus.KEY_PENDING, None)) is None
        assert round_rate(report(value=None)) is None

    def test_median_over_measured_runs_with_silent_runs_as_zero(self) -> None:
        reports = [report(value=0.5), report(value=2.0), report(value=3.0), report(RunStatus.KEY_PENDING, None), report(value=None)]
        assert median_rate(reports) == 2.0
        assert meets_minimum_rate(reports)

    def test_silent_runs_pull_the_median_down(self) -> None:
        """Negative control: three good rounds do not pass when two others delivered nothing or failed."""
        reports = [report(value=5.0), report(value=6.0), report(value=7.0), report(RunStatus.NO_EVENTS, 0.0), report(RunStatus.ERROR, None)]
        assert median_rate(reports) == 5.0
        silent = [report(value=5.0), report(RunStatus.NO_EVENTS, 0.0), report(RunStatus.ERROR, None)]
        assert median_rate(silent) == 0.0
        assert not meets_minimum_rate(silent)

    def test_below_threshold_is_rejected(self) -> None:
        """Negative control: a median of 0.977 events/s does not meet the rule."""
        assert not meets_minimum_rate([report(value=0.977), report(value=0.98), report(value=5.0)])

    def test_no_measurement_is_rejected(self) -> None:
        assert median_rate([report(RunStatus.KEY_PENDING, None)]) is None
        assert not meets_minimum_rate([report(RunStatus.KEY_PENDING, None)])
        assert not meets_minimum_rate([])


class TestVerdict:
    """The median of a planned number of rounds is fixed once no missing rounds can move it across 1 event/s."""

    def test_thirteen_of_twenty_four_at_or_above_one_passes_whatever_follows(self) -> None:
        assert verdict([report(value=1.0)] * 13, 24) is Verdict.PASSES

    def test_twelve_of_twenty_four_at_one_point_five_is_still_open(self) -> None:
        """Negative control: twelve zeros to come would give a median of (0 + 1.5) / 2 = 0.75."""
        assert verdict([report(value=1.5)] * 12, 24) is Verdict.OPEN

    def test_twelve_at_two_already_pass_because_the_lowest_median_is_exactly_one(self) -> None:
        assert verdict([report(value=2.0)] * 12, 24) is Verdict.PASSES

    def test_thirteen_below_one_fails_and_twelve_do_not_yet(self) -> None:
        assert verdict([report(value=0.99)] * 13, 24) is Verdict.FAILS
        assert verdict([report(value=0.99)] * 12, 24) is Verdict.OPEN

    def test_silent_and_failed_rounds_count_as_zero(self) -> None:
        silent = [report(RunStatus.NO_EVENTS, None)] * 7 + [report(RunStatus.ERROR, None)] * 6
        assert verdict(silent, 24) is Verdict.FAILS

    def test_rounds_without_a_measurement_use_up_the_plan_without_a_rate(self) -> None:
        pending = report(RunStatus.KEY_PENDING, None)
        assert verdict([pending, pending], 3) is Verdict.OPEN
        assert verdict([pending, pending, pending], 3) is Verdict.FAILS
        assert verdict([report(value=None), report(value=1.5)], 3) is Verdict.OPEN  # one zero to come: (1.5 + 0) / 2
        assert verdict([report(value=None), report(value=1.5), report(value=1.5)], 4) is Verdict.PASSES

    def test_a_complete_plan_is_the_inclusion_rule(self) -> None:
        mixed = [report(value=v) for v in (0.5, 2.0, 3.0)]
        assert verdict(mixed, 3) is Verdict.PASSES and meets_minimum_rate(mixed)
        low = [report(value=v) for v in (0.5, 0.9, 3.0)]
        assert verdict(low, 3) is Verdict.FAILS and not meets_minimum_rate(low)
        assert verdict(low + [report(value=9.0)] * 3, 3) is Verdict.PASSES  # rounds beyond the plan still count

    def test_nothing_measured_is_open_until_the_plan_ends(self) -> None:
        assert verdict([], 24) is Verdict.OPEN

    def test_the_plan_needs_a_round(self) -> None:
        with pytest.raises(ValueError):
            verdict([], 0)

    def test_reports_are_grouped_by_source_in_round_order(self) -> None:
        a1, a2 = report(value=1.0), report(value=2.0)
        b = RunReport("b", RunStatus.OK, 1, 1.0, 3.0, RateBasis.OBSERVED, 1.0, 0.1, 0.0)
        assert reports_by_source([SamplingRound(1, 0.0, (a1, b)), SamplingRound(2, 1.0, (a2,))]) == {"s": [a1, a2], "b": [b]}


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


NOW = 1_792_000_000.0  # 2026-10-14 UTC


def klass(
    name: str, values: list[object], events: int | None = None, names: frozenset[str] = frozenset(), at: float | None = NOW
) -> FieldClass:
    return classify_field(name, values, events or len(values), names | {name}, at)[0]


class TestClassifyField:
    @pytest.mark.parametrize(
        "values",
        [["2026-10-19"], ["2026-10-19T04:15:00Z", "2026-10-19 04:15"], ["2026-10-19T04:15:00.123456+00:00"], ["2026-10-19T04:15:00-0600"]],
    )
    def test_iso_8601_text_is_a_datetime(self, values: list[object]) -> None:
        assert klass("t", values) is FieldClass.DATETIME

    @pytest.mark.parametrize("unit", [1, 1_000, 1_000_000, 1_000_000_000])
    def test_epoch_numbers_near_the_observation_are_datetimes(self, unit: int) -> None:
        assert klass("t", [NOW * unit, (NOW - 3600) * unit]) is FieldClass.DATETIME

    def test_epoch_needs_every_value_in_one_unit_and_an_observation_time(self) -> None:
        assert klass("t", [NOW, NOW * 1000]) is FieldClass.NUMBER
        assert klass("t", [NOW + 401 * 86400]) is FieldClass.NUMBER
        assert klass("t", [NOW], at=None) is FieldClass.NUMBER

    @pytest.mark.parametrize("values", [["2026-10-19 later"], ["19/10/2026"], ["2026-10-19T04"]])
    def test_text_that_is_not_iso_8601_is_not_a_datetime(self, values: list[object]) -> None:
        assert klass("t", values) is not FieldClass.DATETIME

    def test_compact_dates_near_the_observation_are_datetimes(self) -> None:
        assert klass("d", ["20261019", 20261018]) is FieldClass.DATETIME
        assert klass("d", ["20261019053305"]) is FieldClass.DATETIME
        assert klass("d", ["20261019"], at=None) is FieldClass.NUMBER
        assert klass("d", ["19991019"]) is FieldClass.NUMBER  # too far from the observation
        assert klass("d", ["20261340"]) is FieldClass.NUMBER  # not a calendar date
        assert klass("d", [True]) is FieldClass.CATEGORY

    def test_text_epochs_are_datetimes(self) -> None:
        assert klass("t", [str(int(NOW))]) is FieldClass.DATETIME

    def test_leading_zero_digits_are_codes_not_numbers(self) -> None:
        assert klass("h", ["053306", "0123"]) is FieldClass.CATEGORY
        assert klass("h", ["0.5", "-0.25"]) is FieldClass.NUMBER

    def test_coordinates_need_their_partner_and_a_valid_range(self) -> None:
        pair = frozenset({"pos.lat", "pos.lon"})
        assert klass("pos.lat", [19.4, -90], names=pair) is FieldClass.GEOGRAPHIC
        assert klass("pos.lon", [-99.1, 180], names=pair) is FieldClass.GEOGRAPHIC
        assert klass("Latitude", ["19.4"], names=frozenset({"Longitude"})) is FieldClass.GEOGRAPHIC
        assert classify_field("Latitude", ["19.4"], 1, frozenset({"Latitude", "Longitude"}), NOW)[1] is True
        assert klass("pos.lat", [19.4]) is FieldClass.NUMBER
        assert klass("pos.lat", [91.0], names=pair) is FieldClass.NUMBER
        assert klass("pos.lon", [-181.0], names=pair) is FieldClass.NUMBER
        assert klass("pos.lat", [19.4], names=frozenset({"other.lon"})) is FieldClass.NUMBER
        assert klass("pos.lat", [19.4], names=frozenset({"pos.sub.lon"})) is FieldClass.NUMBER

    def test_numbers_and_numeric_text(self) -> None:
        assert classify_field("p", [1, 2.5], 2, frozenset({"p"}), NOW) == (FieldClass.NUMBER, False)
        assert classify_field("p", ["68000.12", "-1e3", ".5"], 3, frozenset({"p"}), NOW) == (FieldClass.NUMBER, True)
        assert klass("p", ["12a"]) is not FieldClass.NUMBER
        assert klass("p", [True, False]) is FieldClass.CATEGORY

    def test_identifier_needs_many_distinct_values_without_spaces(self) -> None:
        ids = [f"id-{i}" for i in range(30)]
        assert klass("i", ids) is FieldClass.IDENTIFIER
        assert klass("i", ids[:20]) is FieldClass.CATEGORY  # not more distinct values than a category may have
        assert klass("i", [*ids, *ids[:5]]) is FieldClass.IDENTIFIER  # repeats allowed: a vehicle reports many times
        assert klass("i", [f"id {i}" for i in range(30)]) is FieldClass.LABEL

    def test_free_text_needs_length_spaces_and_variety(self) -> None:
        sentence = "a sentence that is clearly longer than thirty characters"
        assert klass("x", [f"{sentence} {i}" for i in range(10)]) is FieldClass.FREE_TEXT
        assert klass("x", [sentence] * 10) is FieldClass.CATEGORY  # 1 distinct value
        assert klass("x", [f"short {i}" for i in range(10)]) is FieldClass.CATEGORY
        assert klass("x", [f"{sentence.replace(' ', '_')}{i}" for i in range(10)]) is FieldClass.CATEGORY

    def test_category_limit_grows_with_the_sample(self) -> None:
        assert category_limit(10) == 20 and category_limit(500) == 25 and category_limit(401) == 21
        assert klass("c", [f"v{i % 22}" for i in range(500)], events=500) is FieldClass.CATEGORY
        assert klass("c", [f"v{i % 22} x" for i in range(100)], events=100) is FieldClass.LABEL

    def test_lists_mappings_mixed_kinds_and_empty(self) -> None:
        assert klass("l", [[1], [2]]) is FieldClass.NESTED
        assert klass("m", [{}]) is FieldClass.NESTED
        assert klass("x", [1, "a"]) is FieldClass.NESTED
        assert classify_field("e", [], 3, frozenset({"e"}), NOW) == (FieldClass.EMPTY, False)


def field(name: str, present: float = 1.0, distinct: int = 1, cls: FieldClass = FieldClass.NUMBER) -> FieldProfile:
    return FieldProfile(name, present, distinct, ("number",), None, None, None, "", cls, False)


class TestNaturalKey:
    def test_single_most_distinct_field_wins(self) -> None:
        payloads = [{"id": i, "k": i % 2} for i in range(4)]
        assert natural_key(payloads, profile_fields(payloads)) == ("id",)

    def test_combination_when_no_single_field_is_unique(self) -> None:
        payloads = [{"a": i // 2, "b": i % 2, "c": 0} for i in range(4)]
        assert natural_key(payloads, profile_fields(payloads)) == ("a", "b")

    def test_skips_partial_nested_and_empty_fields(self) -> None:
        payloads = [{"a": 1, "b": [1]}, {"a": 1, "b": [2], "c": 3}]
        fields = (field("a"), field("b", cls=FieldClass.NESTED), field("c", present=0.5, distinct=1), field("e", cls=FieldClass.EMPTY))
        assert natural_key(payloads, fields) == ()

    def test_identifiers_and_times_are_preferred_over_measurements(self) -> None:
        payloads = [{"id": f"v{i % 3}", "t": f"2026-10-19T04:0{i}:00Z", "lat": float(i), "lon": float(-i)} for i in range(6)]
        assert natural_key(payloads, profile_fields(payloads, observed_at=NOW)) == ("t",)
        fields = (field("lat", distinct=6, cls=FieldClass.GEOGRAPHIC), field("id", distinct=3, cls=FieldClass.IDENTIFIER))
        assert natural_key([{"id": i % 3, "lat": i} for i in range(6)], fields) == ("lat",)
        assert natural_key([{"id": i % 3, "lat": i % 2} for i in range(6)], fields) == ("id", "lat")

    def test_no_key_for_identical_events_or_a_single_event(self) -> None:
        assert natural_key([{"a": 1}, {"a": 1}], (field("a"),)) == ()
        assert natural_key([{"a": 1}], (field("a"),)) == ()


class TestProfileSample:
    def test_sizes_duplicates_key_and_times(self) -> None:
        run = RunReport("s", RunStatus.OK, 3, 1.0, 3.0, RateBasis.OBSERVED, 2.0, 0.1, NOW)
        profile = profile_sample(run, [{"id": 1, "t": NOW}, {"id": 2, "t": NOW}, {"id": 1, "t": NOW}])
        assert profile.events_inspected == 3 and profile.duplicate_ratio == round(1 / 3, 4)
        assert profile.bytes_mean == float(len('{"id":1,"t":1792000000.0}')) and profile.bytes_p95 == len('{"id":1,"t":1792000000.0}')
        assert profile.natural_key == () and {f.name: f.field_class for f in profile.fields}["t"] is FieldClass.DATETIME

    def test_p95_is_nearest_rank_and_text_is_counted_in_utf8_bytes(self) -> None:
        run = RunReport("s", RunStatus.OK, 20, 1.0, 20.0, RateBasis.OBSERVED, 1.0, 0.1, NOW)
        payloads = [{"a": "x" * i} for i in range(19)] + [{"a": "é" * 100}]
        profile = profile_sample(run, payloads)
        assert profile.bytes_p95 == len('{"a":""}') + 18 and max(len(str(p)) for p in payloads) < len('{"a":""}') + 200
        assert profile_sample(run, [{"a": "é"}]).bytes_mean == len('{"a":""}') + 2

    def test_empty_sample(self) -> None:
        run = RunReport("s", RunStatus.NO_EVENTS, 0, 1.0, 0.0, RateBasis.OBSERVED, 0.0, None, NOW)
        assert profile_sample(run, []) == type(profile_sample(run, []))(run, 0, (), None, None, None, ())


def test_error_messages_name_the_missing_piece() -> None:
    assert "nope" in str(UnknownSourceError("nope"))
    err = MissingCredentialError(["K", "P"], "https://x")
    assert err.env_vars == ("K", "P") and str(err) == "missing API credentials K, P (free sign-up: https://x)"


def test_groups_have_one_letter_each_and_only_the_low_rate_group_is_inactive() -> None:
    assert [g.value for g in Group] == ["A", "B", "C", "D", "E"]
    assert [g for g in Group if not g.active] == [Group.LOW_RATE]
