"""Experiment 5a-5c: output style.

Measured on output tokens, not cache tokens (spec, §Experiment 5) — a style
instruction is a small, stable block that caches like any other frozen system
text; what it changes is how much the model writes.
"""

from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agents.fixer import FixerAgent
from hakka_vibe.measurement.arm_runner import ArmSummary, fresh_copy_of, run_arm
from hakka_vibe.seams.output_style import OutputStyle, load_style

ARMS: dict[str, OutputStyle | None] = {
    "5a": None,
    "5b": load_style("caveman"),
    "5c": load_style("ste100"),
}


def run_output_style_experiment(
    client: Anthropic,
    *,
    fixture: Path,
    model: str,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 5a through 5c and return each arm's summary, keyed by arm id."""
    summaries: dict[str, ArmSummary] = {}
    for arm, style in ARMS.items():

        def agent_for(run: int, *, style: OutputStyle | None = style, arm: str = arm) -> FixerAgent:
            return FixerAgent(
                client=client,
                workspace=fresh_copy_of(fixture, arm, run),
                model=model,
                output_style=style,
            )

        kwargs = {"results_root": results_root} if results_root is not None else {}
        summaries[arm] = run_arm(experiment="5", arm=arm, agent_for=agent_for, **kwargs)
    return summaries
