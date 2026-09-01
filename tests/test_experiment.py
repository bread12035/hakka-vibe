"""Arm summary tests.

The statistics are pure, so they are pinned down here without spending a call.
The runner entry that actually executes an arm gets one smoke test and no
unit tests, because every execution is billable.
"""

from decimal import Decimal

import pytest

from hakka_vibe.measurement.run_record import Call, RunRecord
from hakka_vibe.runner import RUNS_PER_ARM, summarise


def record_costing(output_tokens: int, *, passed: bool = True, run: int = 1) -> RunRecord:
    return RunRecord(
        experiment="6",
        arm="6a",
        run=run,
        model="claude-opus-5",
        calls=(
            Call(
                model="claude-opus-5",
                usage={
                    "input_tokens": 0,
                    "output_tokens": output_tokens,
                    "output_tokens_details": None,
                    "cache_read_input_tokens": 0,
                    "cache_creation": None,
                },
            ),
        ),
        passed=passed,
    )


def test_an_arm_reports_its_median_cost() -> None:
    # Opus 5 output is $25.00/MTok, so 1000/2000/3000 tokens cost
    # $0.025 / $0.050 / $0.075. The median of three is the middle one.
    summary = summarise("6a", [record_costing(1_000), record_costing(3_000), record_costing(2_000)])

    assert summary.median_cost == Decimal("0.050")


def test_an_arm_reports_its_spread_alongside_its_median() -> None:
    summary = summarise("6a", [record_costing(1_000), record_costing(3_000), record_costing(2_000)])

    assert summary.lowest_cost == Decimal("0.025")
    assert summary.highest_cost == Decimal("0.075")


def test_an_arm_reports_how_many_of_its_runs_passed() -> None:
    summary = summarise(
        "6a",
        [
            record_costing(1_000, passed=True),
            record_costing(2_000, passed=False),
            record_costing(3_000, passed=True),
        ],
    )

    assert summary.passed == 2
    assert summary.runs == 3


def test_an_arm_summary_refuses_a_run_count_it_was_not_designed_for() -> None:
    with pytest.raises(ValueError, match=str(RUNS_PER_ARM)):
        summarise("6a", [record_costing(1_000), record_costing(2_000)])
