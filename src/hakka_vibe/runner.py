"""Running one arm three times, and summarising what it cost.

One run of an agentic task tells you almost nothing — the same arm varies
between attempts, and a single number invites a claim the data can't support.
"""

import shutil
import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from hakka_vibe.measurement.run_record import DEFAULT_RESULTS_ROOT, RunRecord, write_run_record

RUNS_PER_ARM = 3


@dataclass(frozen=True)
class ArmSummary:
    """What one arm cost, and how much its runs disagreed."""

    arm: str
    runs: int
    passed: int
    median_cost: Decimal
    lowest_cost: Decimal
    highest_cost: Decimal

    @property
    def spread(self) -> Decimal:
        """How far the runs ranged. Reported alongside the median, never instead of it."""
        return self.highest_cost - self.lowest_cost


def summarise(arm: str, records: Sequence[RunRecord]) -> ArmSummary:
    """Reduce an arm's runs to a median, a spread, and a pass count.

    The pass count travels with the cost because cost alone rewards the wrong
    thing: an arm that gives up immediately is the cheapest one there is.
    """
    if len(records) != RUNS_PER_ARM:
        raise ValueError(
            f"an arm is summarised from exactly {RUNS_PER_ARM} runs, got {len(records)}"
        )

    costs = sorted(record.cost.total for record in records)
    return ArmSummary(
        arm=arm,
        runs=len(records),
        passed=sum(1 for record in records if record.passed),
        median_cost=statistics.median(costs),
        lowest_cost=costs[0],
        highest_cost=costs[-1],
    )


def run_arm(
    *,
    experiment: str,
    arm: str,
    run_for: Callable[[int], RunRecord],
    results_root: Path = DEFAULT_RESULTS_ROOT,
) -> ArmSummary:
    """Execute one arm three times, store each run, and summarise them.

    ``run_for`` is called with the run number and must return a finished
    ``RunRecord`` for that run — everything about pointing it at its own
    fresh workspace or varying one experiment knob is the caller's business,
    not this function's.
    """
    records: list[RunRecord] = []
    for run in range(1, RUNS_PER_ARM + 1):
        record = run_for(run)
        write_run_record(record, root=results_root)
        records.append(record)
    return summarise(arm, records)


def fresh_copy_of(fixture: Path, arm: str, run: int) -> Path:
    """A fresh, isolated copy of the fixture for one run of one arm.

    Every experiment needs this: sharing one workspace across runs would leave
    a later run working on whatever an earlier one left behind.
    """
    destination = fixture.parent / f".{fixture.name}-{arm}-{run}"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(fixture, destination)
    return destination
