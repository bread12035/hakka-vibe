"""Experiment 4a-4b: dynamic tool selection (self-built harness).

Both arms carry the same 30 decoy tools the task never calls; they differ
only in whether those decoys are exposed directly (4a) or deferred behind
tool search (4b). The Claude Code half of this experiment is a separate,
manual procedure — see measurement/claude_code_adapter.py for how its
transcripts are graded.
"""

from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agents.fixer import fix
from hakka_vibe.measurement.run_record import RunRecord
from hakka_vibe.runner import ArmSummary, fresh_copy_of, run_arm

DECOY_COUNT = 30


@dataclass(frozen=True)
class ArmConfig:
    decoy_tools: int
    use_tool_search: bool


ARMS: dict[str, ArmConfig] = {
    "4a": ArmConfig(decoy_tools=DECOY_COUNT, use_tool_search=False),
    "4b": ArmConfig(decoy_tools=DECOY_COUNT, use_tool_search=True),
}


def run_tool_search_experiment(
    client: Anthropic,
    *,
    fixture: Path,
    model: str,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 4a and 4b and return each arm's summary, keyed by arm id."""
    summaries: dict[str, ArmSummary] = {}
    for arm, config in ARMS.items():

        def run_for(run: int, *, config: ArmConfig = config, arm: str = arm) -> RunRecord:
            return fix(
                client,
                fresh_copy_of(fixture, arm, run),
                model,
                experiment="4",
                arm=arm,
                run=run,
                decoy_tools=config.decoy_tools,
                use_tool_search=config.use_tool_search,
            )

        kwargs = {"results_root": results_root} if results_root is not None else {}
        summaries[arm] = run_arm(experiment="4", arm=arm, run_for=run_for, **kwargs)
    return summaries
