"""Running an arm, and summarising what its runs cost.

Every arm runs three times. One run of an agentic task tells you almost nothing:
the same arm varies between attempts, and a single number invites a claim the
data cannot support.
"""

import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agent import FixerAgent
from hakka_vibe.run_record import DEFAULT_RESULTS_ROOT, RunRecord, write_run_record

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
        raise ValueError(f"an arm is summarised from exactly {RUNS_PER_ARM} runs, got {len(records)}")

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
    client: Anthropic,
    *,
    experiment: str,
    arm: str,
    workspace_for: Callable[[int], Path],
    model: str,
    results_root: Path = DEFAULT_RESULTS_ROOT,
    max_turns: int = FixerAgent.max_turns,
) -> ArmSummary:
    """Execute one arm three times, store each run, and summarise them.

    ``workspace_for`` is called with the run number and returns a fresh copy of
    the fixture. Each run starts from the same frozen state, or the second run
    would be working on whatever the first one left behind.
    """
    records: list[RunRecord] = []
    for run in range(1, RUNS_PER_ARM + 1):
        agent = FixerAgent(
            client=client,
            workspace=workspace_for(run),
            model=model,
            max_turns=max_turns,
        )
        record = agent.fix(experiment=experiment, arm=arm, run=run)
        write_run_record(record, root=results_root)
        records.append(record)
    return summarise(arm, records)
