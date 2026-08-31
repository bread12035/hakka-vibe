"""Experiment 6e-6f: plan first, then execute.

The comparison point for both arms is 6a-6d (the effort sweep, ticket 06): if
a single planning pass buys back what a lower effort setting alone would
otherwise cost in extra turns, that shows up as 6f's cost sitting closer to
6c/6d's than 6a's plain-low-effort number does.
"""

from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agents.fixer import Effort, FixerAgent
from hakka_vibe.measurement.arm_runner import ArmSummary, fresh_copy_of, run_arm


@dataclass(frozen=True)
class ArmConfig:
    effort: Effort


ARMS: dict[str, ArmConfig] = {
    "6e": ArmConfig(effort="high"),
    "6f": ArmConfig(effort="low"),
}


def build_agent(arm: str, run: int, *, client: Anthropic, fixture: Path, model: str) -> FixerAgent:
    """Construct the agent for one run of one arm. No call — safe to test directly."""
    config = ARMS[arm]
    return FixerAgent(
        client=client,
        workspace=fresh_copy_of(fixture, arm, run),
        model=model,
        effort=config.effort,
        workflow=True,
    )


def run_workflow_decomposition_experiment(
    client: Anthropic,
    *,
    fixture: Path,
    model: str,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 6e and 6f and return each arm's summary, keyed by arm id."""
    summaries: dict[str, ArmSummary] = {}
    for arm in ARMS:

        def agent_for(run: int, *, arm: str = arm) -> FixerAgent:
            return build_agent(arm, run, client=client, fixture=fixture, model=model)

        kwargs = {"results_root": results_root} if results_root is not None else {}
        summaries[arm] = run_arm(experiment="6", arm=arm, agent_for=agent_for, **kwargs)
    return summaries
