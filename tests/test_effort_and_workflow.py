"""Experiment 6a-6f arm configuration tests: what varies per arm, without a call."""

from pathlib import Path

from hakka_vibe.experiments.effort_and_workflow import ARMS
from hakka_vibe.runner import fresh_copy_of


def test_6a_through_6d_cover_the_full_effort_range_with_no_workflow() -> None:
    assert ARMS["6a"].effort == "low"
    assert ARMS["6b"].effort == "medium"
    assert ARMS["6c"].effort == "high"
    assert ARMS["6d"].effort == "xhigh"
    for arm in ("6a", "6b", "6c", "6d"):
        assert ARMS[arm].workflow is False


def test_6e_is_high_effort_with_a_plan() -> None:
    assert ARMS["6e"].effort == "high"
    assert ARMS["6e"].workflow is True


def test_6f_is_low_effort_with_a_plan() -> None:
    # The hypothesis: an explicit plan lets low effort hold up where it
    # otherwise wouldn't — the comparison point is 6a (plain low effort, no
    # plan).
    assert ARMS["6f"].effort == "low"
    assert ARMS["6f"].workflow is True


def test_each_run_gets_its_own_copy_of_the_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "pipeline"
    fixture.mkdir()
    (fixture / "marker.txt").write_text("original")

    first_run = fresh_copy_of(fixture, "6a", 1)
    (first_run / "marker.txt").write_text("mutated by run 1")
    second_run = fresh_copy_of(fixture, "6a", 2)

    assert first_run != second_run
    assert (second_run / "marker.txt").read_text() == "original"
