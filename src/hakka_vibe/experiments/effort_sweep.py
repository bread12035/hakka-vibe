"""Experiment 6a-6d: the effort sweep.

This is the baseline every other experiment is judged against (spec, §Experiment
6). If effort alone buys a large saving, whatever a more elaborate mechanism
saves has to clear that bar to be worth building.
"""

import shutil
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agent import Effort, FixerAgent
from hakka_vibe.experiment import ArmSummary, run_arm

ARMS: dict[str, Effort] = {
    "6a": "low",
    "6b": "medium",
    "6c": "high",
    "6d": "xhigh",
}


def run_effort_sweep(
    client: Anthropic,
    *,
    fixture: Path,
    model: str,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 6a through 6d and return each arm's summary, keyed by arm id."""
    summaries: dict[str, ArmSummary] = {}
    for arm, effort in ARMS.items():

        def agent_for(run: int, *, effort: Effort = effort, arm: str = arm) -> FixerAgent:
            return FixerAgent(
                client=client, workspace=_fresh_copy(fixture, arm, run), model=model, effort=effort
            )

        kwargs = {"results_root": results_root} if results_root is not None else {}
        summaries[arm] = run_arm(experiment="6", arm=arm, agent_for=agent_for, **kwargs)
    return summaries


def _fresh_copy(fixture: Path, arm: str, run: int) -> Path:
    destination = fixture.parent / f".{fixture.name}-{arm}-{run}"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(fixture, destination)
    return destination
