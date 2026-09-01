"""Experiment 6a-6f: thinking cost.

6a-6d is the effort sweep — the baseline every other experiment is judged
against: if effort alone buys a large saving, whatever a more elaborate
mechanism saves has to clear that bar to be worth building.

6e-6f add a planning pass on top of high/low effort: 6f asks whether a low
effort setting paired with an explicit plan can approach 6c/6d's pass rate,
without paying 6c/6d's per-turn reasoning cost.
"""

from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agents.fixer import fix
from hakka_vibe.harness.call import Effort
from hakka_vibe.measurement.run_record import RunRecord
from hakka_vibe.runner import ArmSummary, fresh_copy_of, run_arm


@dataclass(frozen=True)
class ArmConfig:
    effort: Effort
    workflow: bool = False


ARMS: dict[str, ArmConfig] = {
    "6a": ArmConfig(effort="low"),
    "6b": ArmConfig(effort="medium"),
    "6c": ArmConfig(effort="high"),
    "6d": ArmConfig(effort="xhigh"),
    "6e": ArmConfig(effort="high", workflow=True),
    "6f": ArmConfig(effort="low", workflow=True),
}


def run_effort_and_workflow_experiment(
    client: Anthropic,
    *,
    fixture: Path,
    model: str,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 6a through 6f and return each arm's summary, keyed by arm id."""
    summaries: dict[str, ArmSummary] = {}
    for arm, config in ARMS.items():

        def run_for(run: int, *, config: ArmConfig = config, arm: str = arm) -> RunRecord:
            return fix(
                client,
                fresh_copy_of(fixture, arm, run),
                model,
                experiment="6",
                arm=arm,
                run=run,
                effort=config.effort,
                workflow=config.workflow,
            )

        kwargs = {"results_root": results_root} if results_root is not None else {}
        summaries[arm] = run_arm(experiment="6", arm=arm, run_for=run_for, **kwargs)
    return summaries
