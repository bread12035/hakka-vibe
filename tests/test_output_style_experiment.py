"""Output style experiment tests: what's testable without a call."""

from hakka_vibe.experiments.output_style import ARMS


def test_the_baseline_arm_carries_no_style() -> None:
    assert ARMS["5a"] is None


def test_caveman_and_ste100_are_separate_arms_not_merged_into_one() -> None:
    # The spec is explicit: caveman and STE100 differ enough in readability
    # cost that collapsing them into one "has a style" arm would hide that.
    assert ARMS["5b"] is not None
    assert ARMS["5c"] is not None
    assert ARMS["5b"].name != ARMS["5c"].name
    assert ARMS["5b"].instruction != ARMS["5c"].instruction
