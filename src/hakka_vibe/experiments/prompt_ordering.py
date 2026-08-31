"""Experiment 1a-1e: prompt ordering, compaction, and TTL.

1a-1c vary layout only. 1d holds the baseline layout and turns on compaction to
observe cache behaviour once it triggers. 1e holds everything about 1a fixed
except the TTL, so it isolates whether the 1 hour write rate buys back its
2x cost in hit rate.
"""

from dataclasses import dataclass
from pathlib import Path

from anthropic import Anthropic

from hakka_vibe.agents.fixer import FixerAgent
from hakka_vibe.measurement.arm_runner import ArmSummary, fresh_copy_of, run_arm
from hakka_vibe.measurement.call import CacheTtl
from hakka_vibe.seams.prompt_layout import PromptLayout


@dataclass(frozen=True)
class ArmConfig:
    layout: PromptLayout
    cache_ttl: CacheTtl = "5m"
    compaction: bool = False
    max_turns: int = FixerAgent.max_turns


ARMS: dict[str, ArmConfig] = {
    "1a": ArmConfig(layout=PromptLayout.BASELINE),
    "1b": ArmConfig(layout=PromptLayout.DYNAMIC_FIRST),
    "1c": ArmConfig(layout=PromptLayout.STATIC_INTERLEAVED),
    "1d": ArmConfig(layout=PromptLayout.BASELINE, compaction=True, max_turns=80),
    "1e": ArmConfig(layout=PromptLayout.BASELINE, cache_ttl="1h"),
}


def run_prompt_ordering_experiment(
    client: Anthropic,
    *,
    fixture: Path,
    model: str,
    results_root: Path | None = None,
) -> dict[str, ArmSummary]:
    """Run 1a through 1e and return each arm's summary, keyed by arm id."""
    summaries: dict[str, ArmSummary] = {}
    for arm, config in ARMS.items():

        def agent_for(run: int, *, config: ArmConfig = config, arm: str = arm) -> FixerAgent:
            return FixerAgent(
                client=client,
                workspace=fresh_copy_of(fixture, arm, run),
                model=model,
                prompt_layout=config.layout,
                cache_ttl=config.cache_ttl,
                compaction=config.compaction,
                max_turns=config.max_turns,
            )

        kwargs = {"results_root": results_root} if results_root is not None else {}
        summaries[arm] = run_arm(experiment="1", arm=arm, agent_for=agent_for, **kwargs)
    return summaries
