"""Experiment 6a-6d: the effort sweep.

This is the baseline every other experiment is judged against (spec, §Experiment
6). If effort alone buys a large saving, whatever a more elaborate mechanism
saves has to clear that bar to be worth building.
"""

from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agent import Effort, FixerAgent
from hakka_vibe.experiment import ArmSummary, fresh_copy_of, run_arm

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
                client=client, workspace=fresh_copy_of(fixture, arm, run), model=model, effort=effort
            )

        kwargs = {"results_root": results_root} if results_root is not None else {}
        summaries[arm] = run_arm(experiment="6", arm=arm, agent_for=agent_for, **kwargs)
    return summaries

