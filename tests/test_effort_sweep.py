"""Effort sweep tests.

Running the sweep is billable — four arms, three runs each. What is pinned down
here is the part that does not need a call: which arm maps to which effort, and
that each run gets an isolated copy of the fixture rather than a shared one.
"""

from pathlib import Path

from hakka_vibe.experiments.effort_sweep import ARMS, _fresh_copy


def test_the_four_arms_cover_the_full_effort_range() -> None:
    # 6e/6f (the workflow-decomposition arms) are a separate ticket; this
    # sweep is exactly the baseline the spec calls for.
    assert ARMS == {"6a": "low", "6b": "medium", "6c": "high", "6d": "xhigh"}


def test_each_run_gets_its_own_copy_of_the_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "pipeline"
    fixture.mkdir()
    (fixture / "marker.txt").write_text("original")

    first_run = _fresh_copy(fixture, "6a", 1)
    (first_run / "marker.txt").write_text("mutated by run 1")
    second_run = _fresh_copy(fixture, "6a", 2)

    assert first_run != second_run
    assert (second_run / "marker.txt").read_text() == "original"
